"""Research gap identification by comparing RQ with literature.

Analyzes the relationship between the research question and existing
literature to identify:
- Untested IV-DV combinations
- Missing populations or contexts
- Novel vs. derivative research directions
- Under-explored relationships
"""

import logging
from typing import Dict, Any, List, Set
from dataclasses import dataclass

try:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    
    from copilot_workflow.schemas import ResearchQuestion
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    logging.warning("Schema not available for gap analysis")

from Literature_Landscape_Explorer.concept_extraction import ConceptExtractionResult

logger = logging.getLogger(__name__)


@dataclass
class ResearchGap:
    """A specific research gap identified."""
    gap_type: str  # "untested_relationship", "missing_population", "novel_construct"
    description: str
    severity: str  # "high", "medium", "low"
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_type": self.gap_type,
            "description": self.description,
            "severity": self.severity,
            "recommendations": self.recommendations,
        }


@dataclass
class GapAnalysisResult:
    """Results from research gap analysis."""
    gaps: List[ResearchGap]
    novelty_score: float  # 0.0-1.0, how novel is the RQ
    coverage_score: float  # 0.0-1.0, how well-covered by literature
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gaps": [g.to_dict() for g in self.gaps],
            "novelty_score": self.novelty_score,
            "coverage_score": self.coverage_score,
            "summary": self.summary,
        }


def identify_research_gaps(
    rq: ResearchQuestion,
    extraction_result: ConceptExtractionResult,
    graph: Dict[str, List]
) -> GapAnalysisResult:
    """Identify research gaps between RQ and existing literature.
    
    Args:
        rq: Research question to analyze
        extraction_result: Extracted concepts from literature
        graph: Knowledge graph with nodes and edges
        
    Returns:
        GapAnalysisResult with identified gaps and scores
    """
    if not SCHEMA_AVAILABLE:
        logger.warning("Schema not available, returning empty gap analysis")
        return GapAnalysisResult(
            gaps=[],
            novelty_score=0.5,
            coverage_score=0.5,
            summary="Gap analysis unavailable (schema not loaded)"
        )
    
    gaps = []
    
    # Normalize RQ constructs
    rq_constructs = set(c.lower().strip() for c in rq.parsed_constructs)
    
    # Get literature constructs
    lit_constructs = set(c.name.lower().strip() for c in extraction_result.constructs)
    
    # 1. Identify novel constructs (in RQ but not in literature)
    novel_constructs = rq_constructs - lit_constructs
    if novel_constructs:
        gap = ResearchGap(
            gap_type="novel_construct",
            description=f"Novel constructs not well-studied in existing literature: {', '.join(novel_constructs)}",
            severity="high",
            recommendations=[
                "Clearly define these novel constructs in introduction",
                "Justify why these constructs are important",
                "Consider pilot studies to validate construct measures"
            ]
        )
        gaps.append(gap)
    
    # 2. Identify well-studied constructs (overlap)
    common_constructs = rq_constructs & lit_constructs
    if common_constructs and not novel_constructs:
        gap = ResearchGap(
            gap_type="derivative_research",
            description=f"All RQ constructs are well-established: {', '.join(common_constructs)}",
            severity="low",
            recommendations=[
                "Focus on novel combination or context",
                "Emphasize unique population or setting",
                "Consider adding moderators or mediators for novelty"
            ]
        )
        gaps.append(gap)
    
    # 3. Check for untested relationships
    if rq.notes and ("IV" in rq.notes or "DV" in rq.notes):
        # Extract potential IVs and DVs from notes
        untested_rels = _check_untested_relationships(
            rq,
            extraction_result,
            graph
        )
        if untested_rels:
            gaps.extend(untested_rels)
    
    # 4. Check for missing methodological approaches
    method_gaps = _check_methodological_gaps(
        extraction_result,
        rq_constructs
    )
    if method_gaps:
        gaps.extend(method_gaps)
    
    # 5. Calculate novelty score
    novelty_score = _calculate_novelty_score(
        rq_constructs,
        lit_constructs,
        extraction_result
    )
    
    # 6. Calculate coverage score
    coverage_score = _calculate_coverage_score(
        rq_constructs,
        lit_constructs,
        extraction_result
    )
    
    # 7. Generate summary
    summary = _generate_gap_summary(
        gaps,
        novelty_score,
        coverage_score,
        rq_constructs,
        lit_constructs
    )
    
    logger.info(
        f"Gap analysis complete: {len(gaps)} gaps identified, "
        f"novelty={novelty_score:.2f}, coverage={coverage_score:.2f}"
    )
    
    return GapAnalysisResult(
        gaps=gaps,
        novelty_score=novelty_score,
        coverage_score=coverage_score,
        summary=summary
    )


def _check_untested_relationships(
    rq: ResearchQuestion,
    extraction_result: ConceptExtractionResult,
    graph: Dict[str, List]
) -> List[ResearchGap]:
    """Check for untested relationships in the literature.
    
    Args:
        rq: Research question
        extraction_result: Extracted concepts
        graph: Knowledge graph
        
    Returns:
        List of gaps related to untested relationships
    """
    gaps = []
    
    # Extract existing relationships from graph
    existing_relationships = set()
    for edge in graph.get("edges", []):
        rel_tuple = (edge.source.lower(), edge.target.lower(), edge.relation_type)
        existing_relationships.add(rel_tuple)
    
    # Check if RQ constructs have unexplored relationships
    rq_constructs = [c.lower() for c in rq.parsed_constructs]
    
    if len(rq_constructs) >= 2:
        # Check pairwise relationships
        for i, c1 in enumerate(rq_constructs):
            for c2 in rq_constructs[i+1:]:
                # Check if this relationship exists in any form
                found = any(
                    (c1 in rel[0] or c1 in rel[1]) and (c2 in rel[0] or c2 in rel[1])
                    for rel in existing_relationships
                )
                
                if not found:
                    gap = ResearchGap(
                        gap_type="untested_relationship",
                        description=f"Relationship between '{c1}' and '{c2}' not well-established in literature",
                        severity="medium",
                        recommendations=[
                            "Clearly hypothesize the nature of this relationship",
                            "Provide theoretical justification for expected link",
                            "Consider exploratory vs. confirmatory approach"
                        ]
                    )
                    gaps.append(gap)
    
    return gaps


def _check_methodological_gaps(
    extraction_result: ConceptExtractionResult,
    rq_constructs: Set[str]
) -> List[ResearchGap]:
    """Check for methodological gaps.
    
    Args:
        extraction_result: Extracted concepts
        rq_constructs: Research question constructs
        
    Returns:
        List of methodological gaps
    """
    gaps = []
    
    # Check if standard measures exist for RQ constructs
    lit_constructs_with_measures = set()
    for construct in extraction_result.constructs:
        # Check if this construct has associated measures
        has_measure = any(
            construct.name.lower() in m.description.lower()
            for m in extraction_result.measures
        )
        if has_measure:
            lit_constructs_with_measures.add(construct.name.lower())
    
    # Find RQ constructs without established measures
    constructs_without_measures = rq_constructs - lit_constructs_with_measures
    
    if constructs_without_measures:
        gap = ResearchGap(
            gap_type="missing_measures",
            description=f"Limited established measures for: {', '.join(constructs_without_measures)}",
            severity="high",
            recommendations=[
                "Search for or develop validated measurement instruments",
                "Consider adapting existing measures",
                "Plan pilot testing for new measures"
            ]
        )
        gaps.append(gap)
    
    # Check if experimental paradigms exist
    if not extraction_result.paradigms:
        gap = ResearchGap(
            gap_type="limited_paradigms",
            description="Few experimental paradigms found in literature",
            severity="medium",
            recommendations=[
                "Consider innovative experimental designs",
                "Adapt paradigms from related fields",
                "Justify methodological choices clearly"
            ]
        )
        gaps.append(gap)
    
    return gaps


def _calculate_novelty_score(
    rq_constructs: Set[str],
    lit_constructs: Set[str],
    extraction_result: ConceptExtractionResult
) -> float:
    """Calculate how novel the research question is.
    
    Args:
        rq_constructs: RQ constructs
        lit_constructs: Literature constructs
        extraction_result: Extracted concepts
        
    Returns:
        Novelty score (0.0-1.0, higher = more novel)
    """
    if not rq_constructs:
        return 0.5
    
    # Proportion of novel constructs
    novel = rq_constructs - lit_constructs
    novel_ratio = len(novel) / len(rq_constructs)
    
    # Adjust based on construct frequency in literature
    common = rq_constructs & lit_constructs
    if common:
        avg_frequency = sum(
            c.frequency for c in extraction_result.constructs
            if c.name.lower() in common
        ) / len(common)
        
        # Higher frequency = less novel
        frequency_penalty = min(avg_frequency / 10.0, 0.5)
    else:
        frequency_penalty = 0.0
    
    # Combine factors
    novelty = novel_ratio * 0.7 + (1 - frequency_penalty) * 0.3
    
    return min(max(novelty, 0.0), 1.0)


def _calculate_coverage_score(
    rq_constructs: Set[str],
    lit_constructs: Set[str],
    extraction_result: ConceptExtractionResult
) -> float:
    """Calculate how well-covered the RQ is by literature.
    
    Args:
        rq_constructs: RQ constructs
        lit_constructs: Literature constructs
        extraction_result: Extracted concepts
        
    Returns:
        Coverage score (0.0-1.0, higher = better coverage)
    """
    if not rq_constructs:
        return 0.5
    
    # Proportion of RQ constructs found in literature
    overlap = rq_constructs & lit_constructs
    coverage_ratio = len(overlap) / len(rq_constructs)
    
    # Bonus for having frameworks
    framework_bonus = 0.1 if extraction_result.frameworks else 0.0
    
    # Bonus for having measures
    measure_bonus = 0.1 if extraction_result.measures else 0.0
    
    coverage = coverage_ratio * 0.8 + framework_bonus + measure_bonus
    
    return min(max(coverage, 0.0), 1.0)


def _generate_gap_summary(
    gaps: List[ResearchGap],
    novelty_score: float,
    coverage_score: float,
    rq_constructs: Set[str],
    lit_constructs: Set[str]
) -> str:
    """Generate human-readable summary of gap analysis.
    
    Args:
        gaps: Identified gaps
        novelty_score: Novelty score
        coverage_score: Coverage score
        rq_constructs: RQ constructs
        lit_constructs: Literature constructs
        
    Returns:
        Summary text
    """
    summary_parts = []
    
    # Novelty assessment
    if novelty_score > 0.7:
        summary_parts.append("This research question is highly novel, exploring under-studied territory.")
    elif novelty_score > 0.4:
        summary_parts.append("This research question has moderate novelty, building on existing work.")
    else:
        summary_parts.append("This research question addresses well-established topics.")
    
    # Coverage assessment
    if coverage_score > 0.7:
        summary_parts.append("The literature provides strong foundation for this research.")
    elif coverage_score > 0.4:
        summary_parts.append("The literature provides partial foundation; some areas need more support.")
    else:
        summary_parts.append("Limited existing literature found; significant groundwork needed.")
    
    # Construct overlap
    overlap = rq_constructs & lit_constructs
    if overlap:
        summary_parts.append(f"Well-covered constructs: {', '.join(sorted(overlap))}")
    
    novel = rq_constructs - lit_constructs
    if novel:
        summary_parts.append(f"Novel/under-explored constructs: {', '.join(sorted(novel))}")
    
    # Key gaps
    if gaps:
        high_severity = [g for g in gaps if g.severity == "high"]
        if high_severity:
            summary_parts.append(
                f"Critical gaps identified: {len(high_severity)} high-priority areas need attention."
            )
    
    return " ".join(summary_parts)
