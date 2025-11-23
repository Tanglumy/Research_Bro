"""Synthetic Participant Simulator Module.

Generates synthetic participant data to validate experimental designs.
Provides persona modeling, response simulation, and diagnostic feedback.

Module 5 of the Research Copilot workflow.
"""

from .run import run, SyntheticParticipantSimulator
from .persona_modeling import PersonaGenerator, create_personas
from .response_simulator import ResponseSimulator, simulate_responses
from .diagnostics import DiagnosticsEngine

__all__ = [
    'run',
    'SyntheticParticipantSimulator',
    'PersonaGenerator',
    'create_personas',
    'ResponseSimulator',
    'simulate_responses',
    'DiagnosticsEngine'
]

__version__ = '1.0.0'
