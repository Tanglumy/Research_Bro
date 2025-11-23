"""Data models for Research Copilot.

Defines shared data structures used across all research copilot modules.
These models enable smooth transitions between modules and provide
a consistent interface for project state management.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project lifecycle status."""
    CREATED = "created"
    LITERATURE_REVIEW = "literature_review"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    DESIGN_BUILDING = "design_building"
    STIMULUS_GENERATION = "stimulus_generation"
    SIMULATION = "simulation"
    COMPLETED = "completed"


class ResearchQuestion(BaseModel):
    """Research question with parsed constructs."""
    id: str
    raw_text: str
    parsed_constructs: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Operationalization(BaseModel):
    """How a construct is operationalized in research."""
    description: str
    typical_dvs: List[str] = Field(default_factory=list)
    example_studies: List[str] = Field(default_factory=list)


class Concept(BaseModel):
    """A theoretical construct or concept in the knowledge graph."""
    id: str
    label: str
    type: Literal["theoretical_construct", "measure", "paradigm", "population", "outcome"] = "theoretical_construct"
    linked_papers: List[str] = Field(default_factory=list)
    common_measures: List[str] = Field(default_factory=list)
    operationalizations: List[Operationalization] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConceptEdge(BaseModel):
    """Relationship between concepts in knowledge graph."""
    source: str
    target: str
    relation_type: Literal[
        "predicts",
        "associated_with",
        "operationalized_by",
        "measured_by",
        "moderates",
        "mediates"
    ]
    strength: Optional[float] = None
    evidence_papers: List[str] = Field(default_factory=list)


class KnowledgeGraph(BaseModel):
    """Complete knowledge graph for a project."""
    nodes: Dict[str, Concept] = Field(default_factory=dict)
    edges: List[ConceptEdge] = Field(default_factory=list)
    
    def add_node(self, concept: Concept):
        self.nodes[concept.id] = concept
    
    def add_edge(self, edge: ConceptEdge):
        self.edges.append(edge)
    
    def get_connected_concepts(self, concept_id: str) -> List[str]:
        """Get all concepts connected to the given concept."""
        connected = []
        for edge in self.edges:
            if edge.source == concept_id:
                connected.append(edge.target)
            elif edge.target == concept_id:
                connected.append(edge.source)
        return list(set(connected))


class LiteratureGap(BaseModel):
    """Identified gap in existing literature."""
    description: str
    missing_combinations: List[Dict[str, str]] = Field(default_factory=list)
    unexplored_populations: List[str] = Field(default_factory=list)
    methodological_gaps: List[str] = Field(default_factory=list)
    theoretical_gaps: List[str] = Field(default_factory=list)


class LiteratureLandscape(BaseModel):
    """Output from Literature Explorer module."""
    research_question_id: str
    knowledge_graph: KnowledgeGraph
    theoretical_frameworks: List[Dict[str, Any]] = Field(default_factory=list)
    common_measures: Dict[str, List[str]] = Field(default_factory=dict)
    experimental_paradigms: List[Dict[str, Any]] = Field(default_factory=list)
    gaps: LiteratureGap
    summary: str
    citations: List[Dict[str, str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Hypothesis(BaseModel):
    """Structured hypothesis with variables and relationships."""
    id: str
    text: str
    iv: List[str] = Field(default_factory=list, description="Independent variables")
    dv: List[str] = Field(default_factory=list, description="Dependent variables")
    mediators: List[str] = Field(default_factory=list)
    moderators: List[str] = Field(default_factory=list)
    theoretical_basis: List[str] = Field(default_factory=list)
    expected_direction: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    justification: Optional[str] = None


class HypothesisSet(BaseModel):
    """Collection of hypotheses from Hypothesis Engine."""
    research_question_id: str
    hypotheses: List[Hypothesis]
    variable_glossary: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Condition(BaseModel):
    """Experimental condition specification."""
    id: str
    label: str
    manipulation_description: str
    control: bool = False


class Measure(BaseModel):
    """Measurement specification."""
    id: str
    label: str
    scale: Optional[str] = None
    time_points: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class SampleSizePlan(BaseModel):
    """Sample size planning information."""
    assumed_effect_size: Literal["small", "medium", "large"]
    power: float = 0.8
    alpha: float = 0.05
    per_condition_range: List[int]
    total_n_range: List[int]
    justification: Optional[str] = None


class ExperimentDesign(BaseModel):
    """Complete experimental design specification."""
    id: str
    hypothesis_ids: List[str]
    design_type: Literal["between_subjects", "within_subjects", "mixed"]
    conditions: List[Condition]
    measures: List[Measure]
    sample_size_plan: SampleSizePlan
    confound_notes: List[str] = Field(default_factory=list)
    validity_considerations: List[str] = Field(default_factory=list)
    methods_draft: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StimulusMetadata(BaseModel):
    """Metadata annotations for a stimulus."""
    valence: Literal["negative", "neutral", "positive", "mixed"]
    relationship_type: Optional[str] = None
    intensity: Literal["low", "medium", "high"]
    ambiguity_level: Literal["low", "medium", "high"]
    assigned_condition: Optional[str] = None
    language: str = "en"
    word_count: Optional[int] = None
    complexity_score: Optional[float] = None


class StimulusVariant(BaseModel):
    """Variant of a stimulus item."""
    id: str
    variant_type: str
    text: str
    language: str = "en"


class StimulusItem(BaseModel):
    """A single stimulus with variants and metadata."""
    id: str
    text: str
    language: str = "en"
    metadata: StimulusMetadata
    variants: List[StimulusVariant] = Field(default_factory=list)


class StimulusBank(BaseModel):
    """Collection of stimuli from Stimulus Engine."""
    design_id: str
    stimuli: List[StimulusItem]
    balance_report: Dict[str, Any] = Field(default_factory=dict)
    generation_parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PersonaProfile(BaseModel):
    """Synthetic participant persona."""
    attachment_style: Optional[str] = None
    self_criticism: Optional[Literal["low", "medium", "high"]] = None
    culture: Optional[str] = None
    personality_traits: Dict[str, float] = Field(default_factory=dict)
    demographic_info: Dict[str, Any] = Field(default_factory=dict)
    other_traits: Dict[str, Any] = Field(default_factory=dict)


class ParticipantResponse(BaseModel):
    """Simulated response from a synthetic participant."""
    stimulus_id: str
    condition_id: str
    dv_scores: Dict[str, float]
    open_text: Optional[str] = None
    response_time_ms: Optional[int] = None


class SyntheticParticipant(BaseModel):
    """A simulated participant with persona and responses."""
    id: str
    persona: PersonaProfile
    responses: List[ParticipantResponse] = Field(default_factory=list)


class SimulationDiagnostics(BaseModel):
    """Diagnostic information from simulation."""
    dead_variables: List[str] = Field(default_factory=list, description="Variables with no variance")
    weak_manipulations: List[Dict[str, Any]] = Field(default_factory=list)
    condition_means: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    condition_sds: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    effect_estimates: List[Dict[str, Any]] = Field(default_factory=list)


class SimulationResults(BaseModel):
    """Complete simulation output."""
    design_id: str
    participants: List[SyntheticParticipant]
    diagnostics: SimulationDiagnostics
    summary_statistics: Dict[str, Any] = Field(default_factory=dict)
    example_responses: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectState(BaseModel):
    """Complete state of a research project."""
    id: str
    name: str
    status: ProjectStatus = ProjectStatus.CREATED
    research_question: Optional[ResearchQuestion] = None
    literature_landscape: Optional[LiteratureLandscape] = None
    hypothesis_set: Optional[HypothesisSet] = None
    experiment_design: Optional[ExperimentDesign] = None
    stimulus_bank: Optional[StimulusBank] = None
    simulation_results: Optional[SimulationResults] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def update_status(self, new_status: ProjectStatus):
        """Update project status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
