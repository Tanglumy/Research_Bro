"""Research Copilot Backend Service.

An AI-powered research workflow system that takes researchers from
fuzzy ideas to complete experimental designs with synthetic data validation.

Core Components:
- ProjectStateService: Manages project persistence and versioning
- LiteratureExplorer: Extracts concepts and builds knowledge graphs
- HypothesisEngine: Generates structured hypotheses (TODO)
- DesignEngine: Builds experimental designs (TODO)
- StimulusEngine: Generates balanced stimuli (TODO)
- SimulationEngine: Creates synthetic participant data (TODO)

Usage:
    # Start the FastAPI backend
    python -m spoon_ai.research_copilot.api
    
    # Or use uvicorn directly
    uvicorn spoon_ai.research_copilot.api:app --reload

API Documentation:
    Interactive docs available at: http://localhost:8000/docs
"""

from .models import (
    ProjectState,
    ProjectStatus,
    ResearchQuestion,
    Concept,
    KnowledgeGraph,
    LiteratureLandscape,
    Hypothesis,
    HypothesisSet,
    ExperimentDesign,
    StimulusBank,
    SimulationResults
)
from .state_service import ProjectStateService
from .modules import LiteratureExplorer

__version__ = "1.0.0"

__all__ = [
    # Core service
    'ProjectStateService',
    
    # Data models
    'ProjectState',
    'ProjectStatus',
    'ResearchQuestion',
    'Concept',
    'KnowledgeGraph',
    'LiteratureLandscape',
    'Hypothesis',
    'HypothesisSet',
    'ExperimentDesign',
    'StimulusBank',
    'SimulationResults',
    
    # Modules
    'LiteratureExplorer',
]
