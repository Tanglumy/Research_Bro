"""Main entry point for Literature Landscape Explorer module.

Orchestrates paper retrieval, concept extraction, graph building,
and gap analysis to provide a complete literature landscape.
"""

import asyncio
import logging
from typing import Optional

try:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    
    from copilot_workflow.schemas import ProjectState, AuditEntry
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    logging.warning("Schema not available for literature explorer")

from Literature_Landscape_Explorer.paper_retrieval import retrieve_papers
from Literature_Landscape_Explorer.concept_extraction import extract_concepts_from_papers
from Literature_Landscape_Explorer.graph_builder import (
    build_knowledge_graph,
    enrich_graph_with_measures
)
from Literature_Landscape_Explorer.gap_analysis import identify_research_gaps

logger = logging.getLogger(__name__)


async def run(project: ProjectState) -> ProjectState:
    """Run literature landscape exploration.
    
    Takes a ProjectState with research question, retrieves papers,
    extracts concepts, builds knowledge graph, and identifies gaps.
    
    Args:
        project: ProjectState with initialized research question
        
    Returns:
        Updated ProjectState with populated concepts and audit log
    """
    if not SCHEMA_AVAILABLE:
        logger.error("Schema not available, cannot run literature explorer")
        return project
    
    if not project.rq:
        logger.error("No research question provided")
        project.audit_log.append(AuditEntry(
            level="error",
            message="Literature exploration failed: no research question",
            location="literature_explorer"
        ))
        return project
    
    logger.info(f"Starting literature exploration for: {project.rq.raw_text}")
    
    try:
        # 1. Retrieve papers
        logger.info("Step 1/4: Retrieving papers...")
        papers = await retrieve_papers(
            project.rq.parsed_constructs,
            limit=20
        )
        logger.info(f"Retrieved {len(papers)} papers")
        project.papers = papers
        
        if not papers:
            project.audit_log.append(AuditEntry(
                level="warning",
                message="No papers retrieved from academic sources",
                location="literature_explorer",
                details={"constructs": project.rq.parsed_constructs}
            ))
            return project
        
        # 2. Extract concepts
        logger.info("Step 2/4: Extracting concepts from papers...")
        extraction = await extract_concepts_from_papers(papers)
        logger.info(
            f"Extracted {len(extraction.constructs)} constructs, "
            f"{len(extraction.frameworks)} frameworks, "
            f"{len(extraction.measures)} measures, "
            f"{len(extraction.paradigms)} paradigms"
        )
        
        # 3. Build knowledge graph
        logger.info("Step 3/4: Building knowledge graph...")
        graph = build_knowledge_graph(extraction, papers)
        graph = enrich_graph_with_measures(graph, extraction)
        logger.info(
            f"Built graph with {len(graph['nodes'])} nodes, "
            f"{len(graph['edges'])} edges"
        )
        
        # 4. Identify research gaps
        logger.info("Step 4/4: Analyzing research gaps...")
        gaps = identify_research_gaps(project.rq, extraction, graph)
        logger.info(
            f"Identified {len(gaps.gaps)} gaps "
            f"(novelty={gaps.novelty_score:.2f}, coverage={gaps.coverage_score:.2f})"
        )
        
        # 5. Update project state
        project.concepts = graph
        
        # 6. Add comprehensive audit log
        project.audit_log.append(AuditEntry(
            level="info",
            message="Literature landscape exploration complete",
            location="literature_explorer",
            details={
                "papers_retrieved": len(papers),
                "paper_sources": _count_sources(papers),
                "concepts_extracted": {
                    "frameworks": len(extraction.frameworks),
                    "constructs": len(extraction.constructs),
                    "measures": len(extraction.measures),
                    "paradigms": len(extraction.paradigms),
                    "relationships": len(extraction.relationships)
                },
                "graph_stats": {
                    "nodes": len(graph["nodes"]),
                    "edges": len(graph["edges"])
                },
                "gap_analysis": {
                    "gaps_found": len(gaps.gaps),
                    "high_severity_gaps": len([g for g in gaps.gaps if g.severity == "high"]),
                    "novelty_score": gaps.novelty_score,
                    "coverage_score": gaps.coverage_score,
                    "summary": gaps.summary
                },
                "top_constructs": [
                    {"name": c.name, "frequency": c.frequency}
                    for c in extraction.constructs[:5]
                ]
            }
        ))
        
        logger.info("Literature exploration completed successfully")
        return project
        
    except Exception as e:
        logger.error(f"Literature exploration failed: {e}", exc_info=True)
        project.audit_log.append(AuditEntry(
            level="error",
            message=f"Literature exploration failed: {str(e)}",
            location="literature_explorer"
        ))
        return project


def _count_sources(papers) -> dict:
    """Count papers by source.
    
    Args:
        papers: List of Paper objects
        
    Returns:
        Dictionary with source counts
    """
    sources = {}
    for paper in papers:
        source = paper.source
        sources[source] = sources.get(source, 0) + 1
    return sources


async def run_with_summary(project: ProjectState) -> tuple:
    """Run literature explorer and return project plus summary.
    
    Convenience function for testing that returns both the updated
    project and a human-readable summary.
    
    Args:
        project: ProjectState with research question
        
    Returns:
        Tuple of (updated_project, summary_dict)
    """
    project = await run(project)
    
    # Extract summary from audit log
    lit_entry = next(
        (e for e in project.audit_log if e.location == "literature_explorer" and e.level == "info"),
        None
    )
    
    if lit_entry and lit_entry.details:
        summary = {
            "papers": lit_entry.details.get("papers_retrieved", 0),
            "concepts": lit_entry.details.get("concepts_extracted", {}),
            "graph": lit_entry.details.get("graph_stats", {}),
            "gaps": lit_entry.details.get("gap_analysis", {}),
            "top_constructs": lit_entry.details.get("top_constructs", [])
        }
    else:
        # Ensure all keys exist even on error
        summary = {
            "papers": 0,
            "concepts": {},
            "graph": {},
            "gaps": {},
            "top_constructs": [],
            "error": "No summary available"
        }
    
    return project, summary
