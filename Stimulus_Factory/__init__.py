from __future__ import annotations

from typing import List

from copilot_workflow.schemas import (
    ProjectState,
    StimulusItem,
    StimulusMetadata,
    StimulusVariant,
    AuditEntry,
)


async def run(project: ProjectState) -> ProjectState:
    """Stub stimulus module: generate one stimulus per condition with metadata."""
    stimuli: List[StimulusItem] = []
    if project.design:
        for cond in project.design.conditions:
            stimuli.append(
                StimulusItem(
                    text=f"Scenario tailored to {cond.label}",
                    metadata=StimulusMetadata(
                        valence="neutral",
                        intensity="medium",
                        ambiguity_level="low",
                        assigned_condition=cond.id,
                    ),
                    variants=[StimulusVariant(variant_type="original", text=f"Original for {cond.label}")],
                )
            )
    project.stimuli = stimuli
    project.audit_log.append(AuditEntry(message="Stimulus module generated placeholder stimuli", level="info"))
    return project
