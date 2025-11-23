# Copilot Workflow Package

This package wires the five capability modules (Literature Explorer, Hypothesis Generator, Design Builder, Stimulus Factory, Simulation) into a SpoonOS `StateGraph` workflow using shared schemas and a stubbed set of node functions. Replace stub logic with real toolkit/LLM calls as you build out each module.

## Layout
- `schemas.py` — shared Pydantic models for research question, concepts, hypotheses, design, stimuli, personas/simulation, project state, audit entries.
- `workflow.py` — builds the graph, imports module `run()` functions, and provides `run_workflow(prompt)` helper.
- Module dirs: `Literature_Landscape_Explorer/`, `Hypothesis_Generator_Structurer/`, `Experimental_Design_Builder_Critic/`, `Stimulus_Factory/`, `Synthetic_Participant_Simulator/` each export an async `run(project_state)` stub.

## Usage
```python
import asyncio
from copilot_workflow.workflow import run_workflow
asyncio.run(run_workflow("How does attachment anxiety influence emotion regulation?"))
```

## Next steps
- Swap stub `run()` functions for real logic using `spoon_ai` LLM Manager + Spoon Toolkit tools (Research, etc.).
- Add validation/branching for failures (`needs_revision`), checkpoints to persistent storage, and notification hooks.
- Expand schema validation rules and export packaging. 
