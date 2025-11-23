from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

from copilot_workflow.schemas import (
    ProjectState,
    ConceptNode,
    ConceptEdge,
    AuditEntry,
)

logger = logging.getLogger(__name__)

# Ensure toolkit import path is available when run standalone
ROOT = Path(__file__).resolve().parent.parent
TOOLKIT_PATH = ROOT / "spoon-toolkit"
if TOOLKIT_PATH.exists():
    sys.path.append(str(TOOLKIT_PATH))


async def _search_academic(query: str) -> List[dict]:
    try:
        from spoon_toolkits.data_platforms.Research import ResearchAcademicSearchTool  # type: ignore

        tool = ResearchAcademicSearchTool()
        resp = await tool.execute(query=query, limit=5)
        results = []
        if isinstance(resp, dict):
            for key, payload in (resp.get("results") or {}).items():
                if isinstance(payload, dict):
                    for item in payload.get("results", []) or []:
                        results.append(item)
                elif isinstance(payload, list):
                    results.extend(payload)
        return results
    except Exception as exc:  # noqa: BLE001
        logger.warning("Academic search failed: %s", exc)
        return []


async def run(project: ProjectState) -> ProjectState:
    """Literature module: concept mapping + optional academic search enrichment."""
    constructs = project.rq.parsed_constructs if project.rq else []
    nodes: List[ConceptNode] = [
        ConceptNode(id=f"concept_{i}", label=c, type="construct")
        for i, c in enumerate(constructs, start=1)
    ]
    edges: List[ConceptEdge] = [
        ConceptEdge(source=nodes[i].id, target=nodes[j].id, relation_type="associated_with")
        for i in range(len(nodes))
        for j in range(i + 1, len(nodes))
    ]

    citations = await _search_academic(project.rq.raw_text if project.rq else "")
    if citations:
        for node in nodes:
            node.linked_papers = [c.get("link") or c.get("url") or c.get("title", "") for c in citations][:3]
        project.audit_log.append(
            AuditEntry(
                message=f"Literature module retrieved {len(citations)} results from academic search",
                level="info",
            )
        )
    else:
        project.audit_log.append(
            AuditEntry(
                message="Literature module used constructs only (no search results or search failed)",
                level="warning",
            )
        )

    project.concepts = {"nodes": nodes, "edges": edges}
    return project
