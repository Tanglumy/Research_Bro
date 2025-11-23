from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class ResearchQuestion(BaseModel):
    id: str = Field(default_factory=lambda: _uid("rq"))
    raw_text: str
    parsed_constructs: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def ensure_constructs(self) -> "ResearchQuestion":
        if not self.parsed_constructs:
            raise ValueError("parsed_constructs cannot be empty")
        return self


class ConceptNode(BaseModel):
    id: str
    label: str
    type: str
    linked_papers: List[str] = Field(default_factory=list)
    common_measures: List[str] = Field(default_factory=list)
    operationalizations: List[Dict[str, Any]] = Field(default_factory=list)


class ConceptEdge(BaseModel):
    source: str
    target: str
    relation_type: str


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: _uid("hyp"))
    text: str
    iv: List[str]
    dv: List[str]
    mediators: List[str] = Field(default_factory=list)
    moderators: List[str] = Field(default_factory=list)
    theoretical_basis: List[str] = Field(default_factory=list)
    expected_direction: Optional[str] = None

    @model_validator(mode="after")
    def ensure_roles(self) -> "Hypothesis":
        if not self.iv or not self.dv:
            raise ValueError("hypothesis must include at least one IV and one DV")
        return self


class Condition(BaseModel):
    id: str = Field(default_factory=lambda: _uid("cond"))
    label: str
    manipulation_description: Optional[str] = None


class Measure(BaseModel):
    id: str = Field(default_factory=lambda: _uid("measure"))
    label: str
    scale: Optional[str] = None
    time_points: List[str] = Field(default_factory=list)


class SampleSizePlan(BaseModel):
    assumed_effect_size: Optional[str] = None
    per_condition_range: Optional[List[int]] = None


class ExperimentDesign(BaseModel):
    id: str = Field(default_factory=lambda: _uid("design"))
    design_type: str
    conditions: List[Condition]
    measures: List[Measure]
    sample_size_plan: Optional[SampleSizePlan] = None
    confound_notes: List[str] = Field(default_factory=list)
    methods_draft: Optional[str] = None

    @model_validator(mode="after")
    def ensure_minimums(self) -> "ExperimentDesign":
        if len(self.conditions) < 2:
            raise ValueError("design must define at least two conditions")
        return self


class StimulusVariant(BaseModel):
    id: str = Field(default_factory=lambda: _uid("stim_v"))
    variant_type: str
    text: str


class StimulusMetadata(BaseModel):
    valence: Optional[str] = None
    relationship_type: Optional[str] = None
    intensity: Optional[str] = None
    ambiguity_level: Optional[str] = None
    assigned_condition: Optional[str] = None


class StimulusItem(BaseModel):
    id: str = Field(default_factory=lambda: _uid("stim"))
    text: str
    language: str = "en"
    metadata: StimulusMetadata = Field(default_factory=StimulusMetadata)
    variants: List[StimulusVariant] = Field(default_factory=list)


class Persona(BaseModel):
    attachment_style: Optional[str] = None
    self_criticism: Optional[str] = None
    culture: Optional[str] = None
    other_traits: Dict[str, Any] = Field(default_factory=dict)


class SyntheticResponse(BaseModel):
    stimulus_id: str
    condition_id: str
    dv_scores: Dict[str, float]
    open_text: Optional[str] = None


class SyntheticParticipant(BaseModel):
    id: str = Field(default_factory=lambda: _uid("sp"))
    persona: Persona
    responses: List[SyntheticResponse] = Field(default_factory=list)


class SimulationSummary(BaseModel):
    dv_summary: Dict[str, Any] = Field(default_factory=dict)
    dead_vars: List[str] = Field(default_factory=list)
    weak_effects: List[str] = Field(default_factory=list)
    sample_responses: List[str] = Field(default_factory=list)


class AuditEntry(BaseModel):
    message: str
    level: str = "info"
    location: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class ProjectState(BaseModel):
    project_id: str = Field(default_factory=lambda: _uid("proj"))
    rq: Optional[ResearchQuestion] = None
    concepts: Dict[str, List[Any]] = Field(default_factory=lambda: {"nodes": [], "edges": []})
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    design: Optional[ExperimentDesign] = None
    stimuli: List[StimulusItem] = Field(default_factory=list)
    simulation: Optional[SimulationSummary] = None
    audit_log: List[AuditEntry] = Field(default_factory=list)
    checkpoint_id: Optional[str] = None


def validate_project_state(state: ProjectState) -> List[AuditEntry]:
    audits: List[AuditEntry] = []

    def add(level: str, message: str, location: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        audits.append(
            AuditEntry(
                level=level,
                message=message,
                location=location,
                details=details or {},
            )
        )

    if not state.rq:
        add("error", "Research question missing", "rq")
    if state.rq and not state.rq.parsed_constructs:
        add("error", "Research question parsed_constructs empty", "rq.parsed_constructs")
    if state.concepts.get("nodes") is not None and len(state.concepts.get("nodes", [])) == 0:
        add("warning", "Concept graph has no nodes", "concepts.nodes")
    if state.hypotheses and any((not h.iv or not h.dv) for h in state.hypotheses):
        add("error", "One or more hypotheses missing IV or DV", "hypotheses")
    if state.design and len(state.design.conditions) < 2:
        add("error", "Design must include at least two conditions", "design.conditions")
    if state.stimuli and any(not s.metadata.assigned_condition for s in state.stimuli):
        add("warning", "Stimulus missing assigned_condition", "stimuli.metadata.assigned_condition")
    if state.simulation and state.simulation.dead_vars:
        add("warning", "Simulation flagged dead vars", "simulation.dead_vars", {"dead_vars": state.simulation.dead_vars})

    return audits
