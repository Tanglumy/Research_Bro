"""Research Copilot Modules.

Provides the five core capability modules for the research copilot:
1. Literature Explorer - concept extraction and knowledge graph building
2. Hypothesis Engine - structured hypothesis generation
3. Design Engine - experimental design building
4. Stimulus Engine - stimulus generation and balancing
5. Simulation Engine - synthetic participant simulation
"""

from .literature_explorer import LiteratureExplorer
from .hypothesis_engine import HypothesisEngine
from .design_engine import DesignEngine
from .stimulus_engine import StimulusEngine
from .simulation_engine import SimulationEngine

__all__ = [
    'LiteratureExplorer',
    'HypothesisEngine',
    'DesignEngine',
    'StimulusEngine',
    'SimulationEngine'
]
