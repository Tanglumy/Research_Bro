#!/usr/bin/env python3
"""Module 2: Hypothesis Generator & Structurer - Main orchestration.

Orchestrates:
1. Hypothesis generation from knowledge graph
2. Hypothesis validation
3. Export to JSON and markdown
4. Update ProjectState with generated hypotheses
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add paths
root = Path(__file__).resolve().parent.parent
for p in [root / "spoon-core", root / "spoon-toolkit", root]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

from copilot_workflow.schemas import ProjectState, AuditEntry
from .hypothesis_generator import generate_hypotheses, HypothesisGenerationError
from .hypothesis_validator import validate_hypotheses
from .hypothesis_exporter import (
    export_to_json,
    export_to_markdown_table,
    generate_hypothesis_report
)

logger = logging.getLogger(__name__)


class Module2Error(Exception):
    """Raised when Module 2 fails."""
    pass


async def run(project: ProjectState, num_hypotheses: int = 5) -> ProjectState:
    """Run Module 2: Hypothesis Generator & Structurer.
    
    Takes ProjectState with:
    - Research question (from Module 0)
    - Concept nodes and edges (from Module 1)
    
    Produces:
    - 3-5 structured hypotheses with IV/DV/mediators/moderators
    - Validation results
    - JSON and markdown exports
    
    Updates ProjectState:
    - Sets project.hypotheses
    - Adds audit log entries
    
    Args:
        project: ProjectState with RQ and concepts
        num_hypotheses: Target number of hypotheses (default: 5)
        
    Returns:
        Updated ProjectState
        
    Raises:
        Module2Error: If hypothesis generation fails
    """
    logger.info("=" * 80)
    logger.info("MODULE 2: Hypothesis Generator & Structurer - Starting")
    logger.info("=" * 80)
    
    try:
        # Validate inputs
        _validate_inputs(project)
        
        # Step 1: Generate hypotheses
        logger.info("Step 1/3: Generating hypotheses...")
        gen_result = await generate_hypotheses(project, num_hypotheses=num_hypotheses)
        logger.info(f"Generated {len(gen_result.hypotheses)} hypotheses")
        
        # Log to audit trail
        project.audit_log.append(AuditEntry(
            message=f"Generated {len(gen_result.hypotheses)} hypotheses",
            level="info",
            location="Module2.generation",
            details={
                "hypotheses_count": len(gen_result.hypotheses),
                "summary": gen_result.summary[:200]
            }
        ))
        
        # Step 2: Validate hypotheses
        logger.info("Step 2/3: Validating hypotheses...")
        validation_results = validate_hypotheses(gen_result.hypotheses)
        valid_count = sum(1 for r in validation_results if r.is_valid)
        avg_score = sum(r.score for r in validation_results) / len(validation_results) if validation_results else 0.0
        logger.info(f"Validated hypotheses: {valid_count}/{len(gen_result.hypotheses)} valid, avg score={avg_score:.2f}")
        
        # Log validation results
        project.audit_log.append(AuditEntry(
            message=f"Validated hypotheses: {valid_count}/{len(gen_result.hypotheses)} valid",
            level="info" if valid_count > 0 else "warning",
            location="Module2.validation",
            details={
                "valid_count": valid_count,
                "total_count": len(gen_result.hypotheses),
                "avg_quality_score": avg_score
            }
        ))
        
        # Log warnings for invalid hypotheses
        for i, result in enumerate(validation_results, 1):
            if not result.is_valid:
                warnings_str = "; ".join(result.warnings)
                project.audit_log.append(AuditEntry(
                    message=f"Hypothesis {i} validation failed: {warnings_str}",
                    level="warning",
                    location="Module2.validation",
                    details={"hypothesis_id": result.hypothesis.id}
                ))
        
        # Step 3: Export results
        logger.info("Step 3/3: Exporting results...")
        json_export = export_to_json(gen_result.hypotheses)
        markdown_table = export_to_markdown_table(gen_result.hypotheses)
        full_report = generate_hypothesis_report(
            gen_result.hypotheses,
            validation_results,
            gen_result.summary
        )
        
        logger.info("Exports generated:")
        logger.info(f"  - JSON: {len(json_export)} chars")
        logger.info(f"  - Markdown table: {len(markdown_table)} chars")
        logger.info(f"  - Full report: {len(full_report)} chars")
        
        # Update ProjectState
        project.hypotheses = gen_result.hypotheses
        
        # Log success
        project.audit_log.append(AuditEntry(
            message="Module 2 completed successfully",
            level="info",
            location="Module2",
            details={
                "hypotheses_generated": len(gen_result.hypotheses),
                "valid_hypotheses": valid_count,
                "avg_quality_score": avg_score
            }
        ))
        
        logger.info("=" * 80)
        logger.info("MODULE 2: Hypothesis Generator & Structurer - Complete")
        logger.info(f"  - Generated: {len(gen_result.hypotheses)} hypotheses")
        logger.info(f"  - Valid: {valid_count}/{len(gen_result.hypotheses)}")
        logger.info(f"  - Avg Quality: {avg_score:.2f}")
        logger.info("=" * 80)
        
        return project
        
    except HypothesisGenerationError as e:
        logger.error(f"Hypothesis generation failed: {e}")
        project.audit_log.append(AuditEntry(
            message=f"Module 2 failed: {str(e)}",
            level="error",
            location="Module2",
            details={"error": str(e)}
        ))
        raise Module2Error(f"Hypothesis generation failed: {e}")
        
    except Exception as e:
        logger.error(f"Module 2 unexpected error: {e}")
        project.audit_log.append(AuditEntry(
            message=f"Module 2 unexpected error: {str(e)}",
            level="error",
            location="Module2",
            details={"error": str(e)}
        ))
        raise Module2Error(f"Module 2 failed: {e}")


async def run_with_summary(project: ProjectState, num_hypotheses: int = 5) -> tuple[ProjectState, Dict[str, Any]]:
    """Run Module 2 and return summary metrics.
    
    Args:
        project: ProjectState
        num_hypotheses: Target number of hypotheses
        
    Returns:
        Tuple of (updated ProjectState, summary dict)
    """
    # Run main pipeline
    result_project = await run(project, num_hypotheses=num_hypotheses)
    
    # Validate hypotheses
    validation_results = validate_hypotheses(result_project.hypotheses)
    valid_count = sum(1 for r in validation_results if r.is_valid)
    avg_score = sum(r.score for r in validation_results) / len(validation_results) if validation_results else 0.0
    
    # Build summary
    summary = {
        "num_hypotheses": len(result_project.hypotheses),
        "validated": valid_count,
        "export_formats": ["json", "markdown_table", "report"],
        # Backwards/extended metrics
        "hypotheses_generated": len(result_project.hypotheses),
        "valid_hypotheses": valid_count,
        "avg_quality_score": avg_score,
        "with_mediators": sum(1 for h in result_project.hypotheses if h.mediators),
        "with_moderators": sum(1 for h in result_project.hypotheses if h.moderators),
        "unique_ivs": len({v for h in result_project.hypotheses for v in h.iv}),
        "unique_dvs": len({v for h in result_project.hypotheses for v in h.dv}),
        "frameworks": list({fw for h in result_project.hypotheses for fw in h.theoretical_basis})
    }
    
    return result_project, summary


def _validate_inputs(project: ProjectState) -> None:
    """Validate Module 2 inputs.
    
    Args:
        project: ProjectState to validate
        
    Raises:
        Module2Error: If inputs are invalid
    """
    if not project.rq:
        raise Module2Error("Research question missing. Run Module 0 first.")
    
    if not project.rq.parsed_constructs:
        raise Module2Error("No constructs parsed from research question. Run Module 0 first.")
    
    nodes = project.concepts.get("nodes", [])
    if not nodes:
        logger.warning(
            "No concept nodes found from Module 1. "
            "Hypotheses will be generated from research question only."
        )
    else:
        logger.info(f"Found {len(nodes)} concept nodes from Module 1")


if __name__ == "__main__":
    # Test with sample project
    from copilot_workflow.schemas import ResearchQuestion, ConceptNode, ConceptEdge
    
    # Create test project
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="How does attachment anxiety influence emotion regulation strategies in romantic relationships?",
        parsed_constructs=["attachment anxiety", "emotion regulation strategies", "romantic relationships"],
        domain="Social Psychology"
    )
    
    # Mock some concept nodes
    project.concepts = {
        "nodes": [
            ConceptNode(
                id="c1",
                label="Attachment Anxiety",
                type="construct",
                common_measures=["ECR-R Anxiety subscale"]
            ),
            ConceptNode(
                id="c2",
                label="Emotion Regulation",
                type="construct",
                common_measures=["ERQ", "DERS"]
            )
        ],
        "edges": [
            ConceptEdge(
                source="c1",
                target="c2",
                relation_type="predicts"
            )
        ]
    }
    
    # Run Module 2
    result, summary = asyncio.run(run_with_summary(project, num_hypotheses=3))
    
    print("\n" + "="*80)
    print("MODULE 2 TEST RESULTS")
    print("="*80)
    print(f"\nGenerated {summary['hypotheses_generated']} hypotheses")
    print(f"Valid: {summary['valid_hypotheses']}")
    print(f"Avg Quality: {summary['avg_quality_score']:.2f}")
    print(f"\nHypotheses:")
    for i, h in enumerate(result.hypotheses, 1):
        print(f"\n{i}. {h.text}")
        print(f"   IV: {', '.join(h.iv)}")
        print(f"   DV: {', '.join(h.dv)}")
        if h.mediators:
            print(f"   Mediators: {', '.join(h.mediators)}")
        if h.moderators:
            print(f"   Moderators: {', '.join(h.moderators)}")
