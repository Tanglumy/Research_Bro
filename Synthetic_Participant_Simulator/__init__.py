from __future__ import annotations

from typing import List

from copilot_workflow.schemas import (
    ProjectState,
    Persona,
    SyntheticResponse,
    SyntheticParticipant,
    SimulationSummary,
    AuditEntry,
)


async def run(project: ProjectState) -> ProjectState:
    """Stub simulation module: create one synthetic participant with flat responses."""
    responses: List[SyntheticResponse] = []
    for stim in project.stimuli:
        responses.append(
            SyntheticResponse(
                stimulus_id=stim.id,
                condition_id=stim.metadata.assigned_condition or "",
                dv_scores={"Primary DV": 3.5},
                open_text="Simulated response",
            )
        )
    participant = SyntheticParticipant(
        persona=Persona(attachment_style="secure", culture="collectivistic"),
        responses=responses,
    )
    project.simulation = SimulationSummary(
        dv_summary={"Primary DV": {"Condition A": 3.0, "Condition B": 3.5}},
        dead_vars=[],
        weak_effects=[],
        sample_responses=[r.open_text for r in responses if r.open_text],
    )
    project.audit_log.append(AuditEntry(message="Simulation module created synthetic participant sample", level="info"))
    return project
