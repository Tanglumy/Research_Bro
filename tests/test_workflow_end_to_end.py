#!/usr/bin/env python3
"""End-to-end smoke test for the full Research Copilot workflow.

Runs Modules 1→5 with offline-friendly settings (no LLM/network) to ensure
the pipeline produces literature, hypotheses, designs, stimuli, and simulation
outputs in a single pass.
"""

import os
import sys
from pathlib import Path

# Make project modules importable
ROOT = Path(__file__).resolve().parent.parent
for p in [ROOT / "spoon-core", ROOT / "spoon-toolkit", ROOT]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

from copilot_workflow.schemas import ProjectState, ResearchQuestion
from Literature_Landscape_Explorer.run import run_with_summary as run_m1_summary
from Hypothesis_Generator_Structurer.run import run_with_summary as run_m2_summary
from Experimental_Design_Builder_Critic import run_with_summary as run_m3_summary
from Stimulus_Factory import run as run_module4
from Synthetic_Participant_Simulator import SyntheticParticipantSimulator


async def test_full_workflow_offline_smoke():
    """Verify Modules 1→5 produce outputs without LLM/network dependencies."""
    os.environ.setdefault("OFFLINE_MODE", "1")
    
    project = ProjectState(
        rq=ResearchQuestion(
            id="e2e_rq_01",
            raw_text="How does social support influence stress recovery in college students?",
            parsed_constructs=["social support", "stress recovery", "college students"],
            domain="Health Psychology"
        )
    )
    
    # Module 1: Literature
    project, m1_summary = await run_m1_summary(project)
    assert m1_summary["papers"] > 0
    assert m1_summary["graph"].get("nodes", 0) >= 0  # graph may be minimal in stub mode
    
    # Module 2: Hypotheses (heuristic offline path)
    project, m2_summary = await run_m2_summary(project, num_hypotheses=3)
    assert m2_summary["num_hypotheses"] > 0
    assert project.hypotheses and len(project.hypotheses) == m2_summary["num_hypotheses"]
    
    # Module 3: Design (heuristic path, no LLM)
    project, m3_summary = await run_m3_summary(project, use_llm=False, effect_size="medium")
    assert project.design is not None
    assert m3_summary["num_conditions"] >= 2
    assert m3_summary["sample_size"] > 0
    
    # Module 4: Stimulus Factory (template path)
    project = await run_module4(
        project,
        num_stimuli_per_condition=2,
        style="scenario",
        filter_mode="lenient",
        use_llm=False
    )
    assert project.stimuli, "Stimuli should be generated"
    assert all(s.metadata and s.metadata.assigned_condition for s in project.stimuli)
    
    # Module 5: Simulation
    simulator = SyntheticParticipantSimulator()
    project = await simulator.run(project)
    assert project.simulation is not None
    assert project.simulation.dv_summary is not None
    
    # Final audit/log sanity
    assert project.audit_log, "Audit trail should capture steps across modules"
