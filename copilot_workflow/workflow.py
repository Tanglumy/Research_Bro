from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent.parent
SPOON_CORE_PATH = ROOT / "spoon-core"
SPOON_TOOLKIT_PATH = ROOT / "spoon-toolkit"
for p in (SPOON_CORE_PATH, SPOON_TOOLKIT_PATH):
    if p.exists():
        sys.path.append(str(p))

from spoon_ai.graph import StateGraph, InMemoryCheckpointer  # type: ignore

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    Hypothesis,
    ExperimentDesign,
    StimulusItem,
    SimulationSummary,
    AuditEntry,
    validate_project_state,
)
from Literature_Landscape_Explorer import run as run_literature
from Hypothesis_Generator_Structurer import run as run_hypotheses
from Experimental_Design_Builder_Critic import run as run_design
from Stimulus_Factory import run as run_stimuli
from Synthetic_Participant_Simulator import run as run_simulation


def _checkpoint() -> str:
    return datetime.utcnow().isoformat()


async def ingest_rq(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract research constructs from user query using LLM."""
    import json
    from spoon_ai.llm import LLMManager, ConfigurationManager
    from spoon_ai.schema import Message
    
    text = state.get("input") or ""
    if not text.strip():
        raise ValueError("Research question cannot be empty")
    
    llm = LLMManager(ConfigurationManager())
    
    # LLM prompt for construct extraction
    prompt = f"""Analyze this research question and extract key psychological/behavioral constructs:

Question: {text}

Provide:
1. Main constructs (2-5 key concepts that are central to the research)
2. Research domain (e.g., emotion regulation, attachment, social cognition, decision-making)
3. Potential independent variables (what might be manipulated or compared)
4. Potential dependent variables (what might be measured as outcomes)

Return ONLY valid JSON in this exact format:
{{
  "constructs": ["construct1", "construct2", ...],
  "domain": "research domain",
  "potential_iv": ["var1", "var2"],
  "potential_dv": ["var1", "var2"]
}}"""
    
    try:
        response = await llm.chat(
            [Message(role="user", content=prompt)],
            provider="openai"
        )
        
        # Parse LLM response (handle markdown code fences)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        parsed_data = json.loads(content)
        
        # Validate required fields
        if not parsed_data.get("constructs"):
            parsed_data["constructs"] = ["general construct"]
        if not parsed_data.get("domain"):
            parsed_data["domain"] = "behavioral science"
        
        # Create ResearchQuestion with enriched data
        rq = ResearchQuestion(
            raw_text=text,
            parsed_constructs=parsed_data["constructs"],
            domain=parsed_data.get("domain"),
            notes=f"Potential IVs: {parsed_data.get('potential_iv', [])}, DVs: {parsed_data.get('potential_dv', [])}"
        )
        
        project: ProjectState = state.get("project") or ProjectState()
        project.rq = rq
        project.checkpoint_id = _checkpoint()
        
        # Add audit log entry
        project.audit_log.append(AuditEntry(
            level="info",
            message="Research question ingested and analyzed",
            location="ingest_rq",
            details={
                "constructs": rq.parsed_constructs,
                "domain": rq.domain,
                "potential_variables": {
                    "iv": parsed_data.get("potential_iv", []),
                    "dv": parsed_data.get("potential_dv", [])
                }
            }
        ))
        
        return {"project": project}
        
    except Exception as e:
        # Fallback to basic parsing if LLM fails
        parsed = [part.strip() for part in text.split()[:3] if part.strip()] or ["construct"]
        rq = ResearchQuestion(raw_text=text, parsed_constructs=parsed)
        project: ProjectState = state.get("project") or ProjectState()
        project.rq = rq
        project.checkpoint_id = _checkpoint()
        project.audit_log.append(AuditEntry(
            level="warning",
            message=f"LLM parsing failed, used fallback: {str(e)}",
            location="ingest_rq"
        ))
        return {"project": project}


async def literature_node(state: Dict[str, Any]) -> Dict[str, Any]:
    project: ProjectState = state["project"]
    project = await run_literature(project)
    project.checkpoint_id = _checkpoint()
    return {"project": project}


async def hypotheses_node(state: Dict[str, Any]) -> Dict[str, Any]:
    project: ProjectState = state["project"]
    project = await run_hypotheses(project)
    project.checkpoint_id = _checkpoint()
    return {"project": project}


async def design_node(state: Dict[str, Any]) -> Dict[str, Any]:
    project: ProjectState = state["project"]
    project = await run_design(project)
    project.checkpoint_id = _checkpoint()
    return {"project": project}


async def stimuli_node(state: Dict[str, Any]) -> Dict[str, Any]:
    project: ProjectState = state["project"]
    project = await run_stimuli(project)
    project.checkpoint_id = _checkpoint()
    return {"project": project}


async def simulate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    project: ProjectState = state["project"]
    project = await run_simulation(project)
    project.checkpoint_id = _checkpoint()
    return {"project": project}


async def review_export_node(state: Dict[str, Any]) -> Dict[str, Any]:
    project: ProjectState = state["project"]
    audits = validate_project_state(project)
    if audits:
        project.audit_log.extend(audits)
    bundle = {
        "project_id": project.project_id,
        "checkpoint_id": project.checkpoint_id,
        "hypotheses": len(project.hypotheses),
        "stimuli": len(project.stimuli),
        "conditions": [c.label for c in (project.design.conditions if project.design else [])],
    }
    return {"project": project, "validation": audits, "export_bundle": bundle}


def build_workflow(checkpointer: Optional[InMemoryCheckpointer] = None) -> StateGraph:
    graph = StateGraph(dict, checkpointer=checkpointer)
    graph.add_node("ingest_rq", ingest_rq)
    graph.add_node("literature", literature_node)
    graph.add_node("hypotheses", hypotheses_node)
    graph.add_node("design", design_node)
    graph.add_node("stimuli", stimuli_node)
    graph.add_node("simulate", simulate_node)
    graph.add_node("review_export", review_export_node)

    graph.set_entry_point("ingest_rq")
    graph.add_edge("ingest_rq", "literature")
    graph.add_edge("ingest_rq", "literature")
    graph.add_edge("literature", "hypotheses")
    graph.add_edge("hypotheses", "design")
    graph.add_edge("design", "stimuli")
    graph.add_edge("stimuli", "simulate")
    graph.add_edge("simulate", "review_export")
    return graph


async def run_workflow(prompt: str) -> Dict[str, Any]:
    graph = build_workflow()
    compiled = graph.compile()
    initial_state = {"input": prompt, "project": ProjectState()}
    try:
        return await compiled.invoke(initial_state)
    except ValidationError as e:
        return {"error": str(e)}
