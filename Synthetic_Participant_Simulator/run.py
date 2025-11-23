"""Synthetic Participant Simulator - Main Module.

Generates synthetic participant data to validate experimental designs.
Creates persona-based responses and provides diagnostic feedback.
"""

import logging
import uuid
from typing import List, Dict, Any
import random
import statistics

from copilot_workflow.schemas import (
    ProjectState,
    Persona,
    SyntheticResponse,
    SyntheticParticipant,
    SimulationSummary,
    AuditEntry,
    ExperimentDesign,
    StimulusItem
)

from .persona_modeling import create_personas, PersonaGenerator
from .response_simulator import ResponseSimulator
from .diagnostics import DiagnosticsEngine

logger = logging.getLogger(__name__)


class SyntheticParticipantSimulator:
    """Main simulator class coordinating all simulation components."""
    
    def __init__(self):
        """Initialize the simulator."""
        self.persona_generator = PersonaGenerator()
        self.response_simulator = ResponseSimulator()
        self.diagnostics_engine = DiagnosticsEngine()
        logger.info("SyntheticParticipantSimulator initialized")
    
    async def run(self, project: ProjectState) -> ProjectState:
        """Execute the complete simulation workflow.
        
        Args:
            project: Current project state with design and stimuli
            
        Returns:
            Updated project state with simulation results
        """
        logger.info("Starting synthetic participant simulation")
        
        try:
            # Validate inputs
            if not project.design:
                raise ValueError("No experimental design found. Run design module first.")
            
            if not project.stimuli or len(project.stimuli) == 0:
                raise ValueError("No stimuli found. Run stimulus module first.")
            
            # Step 1: Create persona templates
            logger.info("Creating persona templates...")
            n_participants = self._get_sample_size(project.design)
            personas = self.persona_generator.create_personas(
                n_participants=n_participants,
                design=project.design
            )
            project.audit_log.append(AuditEntry(
                message=f"Generated {len(personas)} persona templates",
                level="info"
            ))
            
            # Step 2: Simulate responses for each participant
            logger.info(f"Simulating responses for {len(personas)} participants...")
            participants = []
            
            for persona in personas:
                participant = await self._simulate_participant(
                    persona=persona,
                    design=project.design,
                    stimuli=project.stimuli
                )
                participants.append(participant)
            
            project.audit_log.append(AuditEntry(
                message=f"Simulated {len(participants)} participants",
                level="info"
            ))
            
            # Step 3: Compute diagnostics
            logger.info("Computing diagnostics...")
            diagnostics = self.diagnostics_engine.compute_diagnostics(
                participants=participants,
                design=project.design
            )
            
            # Step 4: Generate sample responses
            sample_responses = self._extract_sample_responses(participants, n_samples=10)
            weak_effects_raw = diagnostics.get("weak_effects", [])
            weak_effects = [
                (
                    f"{w.get('cond_a', '?')} vs {w.get('cond_b', '?')} "
                    f"on {w.get('dv', '?')} (d={w.get('effect_size', '?')})"
                )
                if isinstance(w, dict) else str(w)
                for w in weak_effects_raw
            ]
            
            # Step 5: Create simulation summary
            project.simulation = SimulationSummary(
                dv_summary=diagnostics["condition_means"],
                dead_vars=diagnostics["dead_variables"],
                weak_effects=weak_effects,
                sample_responses=sample_responses
            )
            
            # Store participants (optional - could be too large for full project state)
            # For now, we'll just store summary statistics
            
            project.audit_log.append(AuditEntry(
                message=f"Simulation complete: {len(diagnostics['dead_variables'])} dead vars, "
                       f"{len(diagnostics['weak_effects'])} weak effects detected",
                level="info"
            ))
            
            logger.info("Synthetic participant simulation completed successfully")
            return project
            
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}")
            project.audit_log.append(AuditEntry(
                message=f"Simulation module error: {str(e)}",
                level="error"
            ))
            raise
    
    def _get_sample_size(self, design: ExperimentDesign) -> int:
        """Determine sample size from design.
        
        Args:
            design: Experimental design
            
        Returns:
            Number of participants to simulate
        """
        # Use sample size plan if available
        if design.sample_size_plan and design.sample_size_plan.per_condition_range:
            # Use middle of range times number of conditions
            per_condition = sum(design.sample_size_plan.per_condition_range) // 2
            n_conditions = len(design.conditions)
            return per_condition * n_conditions
        
        # Default: 50 per condition
        return 50 * len(design.conditions)
    
    async def _simulate_participant(
        self,
        persona: Persona,
        design: ExperimentDesign,
        stimuli: List[StimulusItem]
    ) -> SyntheticParticipant:
        """Simulate responses for one participant.
        
        Args:
            persona: Participant persona
            design: Experimental design
            stimuli: List of stimuli
            
        Returns:
            SyntheticParticipant with all responses
        """
        # Assign participant to condition(s)
        if design.design_type == "between_subjects":
            # Random assignment to one condition
            assigned_condition = random.choice(design.conditions).id
            relevant_stimuli = [
                s for s in stimuli 
                if s.metadata.assigned_condition == assigned_condition
            ]
        elif design.design_type == "within_subjects":
            # Participant sees all conditions
            relevant_stimuli = stimuli
        else:  # mixed
            # For simplicity, treat as within
            relevant_stimuli = stimuli
        
        # Generate responses
        responses = []
        for stimulus in relevant_stimuli:
            response = await self.response_simulator.simulate_response(
                persona=persona,
                stimulus=stimulus,
                design=design
            )
            responses.append(response)
        
        return SyntheticParticipant(
            persona=persona,
            responses=responses
        )
    
    def _extract_sample_responses(self, participants: List[SyntheticParticipant], n_samples: int = 10) -> List[str]:
        """Extract sample open-text responses for inspection.
        
        Args:
            participants: List of synthetic participants
            n_samples: Number of samples to extract
            
        Returns:
            List of sample response texts
        """
        all_responses = []
        for p in participants:
            for r in p.responses:
                if r.open_text:
                    all_responses.append(r.open_text)
        
        # Sample randomly
        if len(all_responses) > n_samples:
            return random.sample(all_responses, n_samples)
        return all_responses


# Module entry point
async def run(project: ProjectState) -> ProjectState:
    """Run the Synthetic Participant Simulator module.
    
    Args:
        project: Current project state
        
    Returns:
        Updated project state with simulation results
    """
    simulator = SyntheticParticipantSimulator()
    return await simulator.run(project)
