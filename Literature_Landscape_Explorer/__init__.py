"""Module 1: Literature Landscape Explorer

Retrieves papers, extracts concepts, builds knowledge graph, identifies research gaps.

Main Functions:
- run(project) -> ProjectState: Main orchestration function
- run_with_summary(project) -> (ProjectState, summary): Run with metrics
"""

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


# Import run and run_with_summary from run module
from .run import run, run_with_summary

# Export for external use
__all__ = [
    "run",
    "run_with_summary",
]
