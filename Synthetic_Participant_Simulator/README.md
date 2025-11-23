# Synthetic Participant Simulator

**Module 5 of Research Copilot Workflow**

Generates synthetic participant data to validate experimental designs before running actual studies. Creates diverse persona-based responses and provides diagnostic feedback on design quality.

## Overview

The Synthetic Participant Simulator helps researchers:
- **Validate experimental designs** with realistic simulated data
- **Identify design problems** (dead variables, weak manipulations)
- **Estimate effect sizes** before data collection
- **Generate sample responses** for qualitative inspection
- **Test design assumptions** with diverse participant profiles

## Features

### 1. Persona Modeling
- Creates diverse participant profiles with:
  - **Attachment styles**: secure, anxious, avoidant, fearful-avoidant
  - **Personality traits**: Big Five dimensions (0-100 scale)
  - **Self-criticism levels**: low, medium, high
  - **Cultural backgrounds**: individualistic, collectivistic, mixed
  - **Demographics**: age, gender, education, relationship status
  - **Psychological characteristics**: stress level, social support

- Ensures balanced distribution across key characteristics
- Generates realistic trait correlations (e.g., anxious attachment + high neuroticism)

### 2. Response Simulation
- Simulates participant responses based on:
  - **Persona characteristics** (personality, attachment style, etc.)
  - **Stimulus properties** (valence, intensity, relationship type)
  - **Design structure** (between/within/mixed designs)

- Generates:
  - **Quantitative DV scores** (Likert scales, continuous measures)
  - **Qualitative text responses** (template-based with persona variation)
  - **Response patterns** consistent with psychological theory

### 3. Diagnostic Engine
- Computes comprehensive statistics:
  - **Condition means and SDs** for each DV
  - **Effect size estimates** (Cohen's d)
  - **Dead variable detection** (insufficient variance)
  - **Weak effect identification** (small between-condition differences)

- Provides actionable feedback:
  - Which DVs show no variation
  - Which condition comparisons have negligible effects
  - Expected effect sizes for power analysis

## Architecture

```
Synthetic_Participant_Simulator/
├── __init__.py              # Module exports
├── run.py                   # Main orchestrator
├── persona_modeling.py      # Persona generation
├── response_simulator.py    # Response generation
├── diagnostics.py           # Statistics & diagnostics
└── README.md               # This file
```

## Usage

### Basic Usage (via Workflow)

```python
import asyncio
from copilot_workflow.schemas import ProjectState
from Synthetic_Participant_Simulator import run

# Assuming project has design and stimuli
project = ProjectState(...)

# Run simulation
project = await run(project)

# Access results
print(f"Dead variables: {project.simulation.dead_vars}")
print(f"Weak effects: {len(project.simulation.weak_effects)}")
print(f"Sample responses: {project.simulation.sample_responses[:3]}")
```

### Advanced Usage (Component-Level)

#### 1. Generate Personas

```python
from Synthetic_Participant_Simulator import PersonaGenerator
from copilot_workflow.schemas import ExperimentDesign

generator = PersonaGenerator()
personas = generator.create_personas(
    n_participants=100,
    design=experiment_design
)

# Inspect persona characteristics
for persona in personas[:5]:
    print(f"Attachment: {persona.attachment_style}")
    print(f"Neuroticism: {persona.personality_traits['neuroticism']}")
    print(f"Self-criticism: {persona.self_criticism}")
```

#### 2. Simulate Responses

```python
from Synthetic_Participant_Simulator import ResponseSimulator

simulator = ResponseSimulator()

# Simulate single response
response = await simulator.simulate_response(
    persona=persona,
    stimulus=stimulus_item,
    design=experiment_design
)

print(f"DV scores: {response.dv_scores}")
print(f"Open text: {response.open_text}")
```

#### 3. Compute Diagnostics

```python
from Synthetic_Participant_Simulator import DiagnosticsEngine

diagnostics = DiagnosticsEngine()
results = diagnostics.compute_diagnostics(
    participants=synthetic_participants,
    design=experiment_design
)

# Condition means
for dv_name, cond_stats in results['condition_means'].items():
    print(f"\n{dv_name}:")
    for cond_id, stats in cond_stats.items():
        print(f"  {cond_id}: M={stats['mean']}, SD={stats['sd']}")

# Effect sizes
for effect in results['effect_estimates']:
    print(f"{effect['dv']}: {effect['condition1']} vs {effect['condition2']}")
    print(f"  Cohen's d = {effect['cohens_d']} ({effect['interpretation']})")
```

## Simulation Logic

### Persona Generation

1. **Balanced Distribution**: Ensures equal representation across attachment styles
2. **Trait Coherence**: Adjusts personality traits based on attachment style
   - Anxious: +15% neuroticism, -10% extraversion
   - Avoidant: -10% openness, -10% agreeableness
   - Secure: +10% agreeableness, -10% neuroticism
3. **Realistic Correlations**: Self-criticism correlates with neuroticism
4. **Demographic Diversity**: Random age (18-65), gender, education, relationship status

### Response Generation

#### Quantitative Scores (DV)

```
Base Score = 4.0 (midpoint of 1-7 scale)

Adjustments:
+ Stimulus valence effect:
  - Negative: +neuroticism*2.0, +0.8 (if anxious)
  - Positive: -0.5, -0.5 (if secure)
  
+ Intensity multiplier:
  - Low: 0.5x
  - Medium: 1.0x
  - High: 1.5x

+ Self-criticism effect (for anxiety/stress DVs):
  - High: +0.7
  - Low: -0.5

+ Individual noise: N(0, 0.5)

Final = clamp(adjusted_score, 1.0, 7.0)
```

#### Qualitative Text

- **Template-based** generation with persona variation
- **Attachment style** determines response pattern:
  - Anxious: worrying, rumination, seeking reassurance
  - Avoidant: distancing, self-reliance, minimal elaboration
  - Secure: balanced, open communication, coping confidence
  - Fearful-avoidant: ambivalence, mixed feelings, approach-avoidance

- **Personality modulation**:
  - High openness → longer, more elaborate responses
  - High extraversion → more social/interpersonal focus

### Diagnostic Thresholds

- **Dead Variable**: SD < 0.3 across all conditions
- **Weak Effect**: |Cohen's d| < 0.3 between conditions
- **Effect Size Interpretation**:
  - Negligible: |d| < 0.2
  - Small: 0.2 ≤ |d| < 0.5
  - Medium: 0.5 ≤ |d| < 0.8
  - Large: |d| ≥ 0.8

## Output Structure

### SimulationSummary

```python
class SimulationSummary:
    dv_summary: Dict[str, Dict[str, Dict[str, float]]]
    # {dv_name: {condition_id: {mean, sd, n}}}
    
    dead_vars: List[str]
    # List of DV names with insufficient variance
    
    weak_effects: List[Dict[str, Any]]
    # [{dv, condition1, condition2, cohens_d, message}]
    
    sample_responses: List[str]
    # Sample of open-text responses for inspection
```

### Example Output

```json
{
  "dv_summary": {
    "State Anxiety": {
      "negative_high": {"mean": 5.23, "sd": 0.87, "n": 50},
      "negative_low": {"mean": 4.12, "sd": 0.92, "n": 50},
      "positive": {"mean": 3.45, "sd": 0.78, "n": 50}
    }
  },
  "dead_vars": [],
  "weak_effects": [
    {
      "dv": "Self-Compassion",
      "condition1": "negative_low",
      "condition2": "negative_high",
      "cohens_d": 0.18,
      "message": "Weak effect between negative_low and negative_high on Self-Compassion"
    }
  ],
  "sample_responses": [
    "This situation really worries me. I feel anxious and can't stop thinking about what might go wrong.",
    "I feel stressed about this, but I think I could manage it with support if needed.",
    "I don't think this would affect me much. I prefer to handle things independently."
  ]
}
```

## Integration with Workflow

### Prerequisites

1. **Experimental Design** (Module 3 output)
   - Design type (between/within/mixed)
   - Conditions defined
   - Measures specified
   - Sample size plan

2. **Stimulus Bank** (Module 4 output)
   - Stimuli with metadata
   - Condition assignments
   - Balanced across conditions

### Workflow Position

Module 5 runs after:
- Module 1: Literature Landscape Explorer
- Module 2: Hypothesis Generator
- Module 3: Design Builder
- Module 4: Stimulus Factory

Output feeds into:
- **Design Refinement**: Identify and fix weak manipulations
- **Power Analysis**: Use effect size estimates for sample size planning
- **Preregistration**: Document expected patterns
- **Pilot Testing**: Compare real data to synthetic baseline

## Configuration

No external API keys required. All simulation is rule-based and deterministic (with controlled randomness).

### Adjustable Parameters

```python
class DiagnosticsEngine:
    DEAD_VAR_THRESHOLD = 0.3  # Adjust for stricter/looser detection
    WEAK_EFFECT_THRESHOLD = 0.3  # Adjust for effect size sensitivity
```

```python
class ResponseSimulator:
    # Adjust base scores, adjustment factors, noise levels in:
    # _generate_dv_score() method
```

## Validation & Testing

### Unit Tests

```bash
pytest tests/test_simulation.py -v
```

Tests cover:
- Persona generation (distribution, trait coherence)
- Response simulation (score ranges, text generation)
- Diagnostics (dead vars, effect sizes, statistics)
- End-to-end simulation workflow

### Integration Tests

```bash
pytest tests/test_workflow_integration.py -k simulation
```

## Limitations & Future Enhancements

### Current Limitations

1. **Simplified Response Model**: Rule-based rather than learned from real data
2. **Limited Persona Diversity**: Fixed set of attachment styles and traits
3. **No Longitudinal Effects**: Assumes independence across responses
4. **Template-Based Text**: Qualitative responses follow patterns rather than free generation

### Planned Enhancements

1. **LLM-Generated Responses**: Use language models for more realistic text
2. **Learned Response Functions**: Train on real data to improve score generation
3. **Extended Persona Characteristics**: Add more psychological dimensions
4. **Longitudinal Modeling**: Simulate within-person change over time
5. **Interactive Refinement**: Allow users to adjust simulation parameters iteratively
6. **Validation Against Real Data**: Compare synthetic to actual pilot data

## Best Practices

### When to Use Simulation

✅ **Good Use Cases:**
- Test design before data collection
- Identify obvious design flaws (dead variables, weak manipulations)
- Estimate approximate effect sizes
- Generate example responses for IRB/ethics review
- Compare alternative design options

❌ **Not Recommended For:**
- Replacing pilot studies
- Precise power calculations (use traditional methods)
- Claiming "data-driven" results (synthetic data is not real data)
- Publishing as actual findings

### Interpreting Results

1. **Dead Variables**: Serious problem - redesign measure or remove
2. **Weak Effects**: Consider:
   - Increasing manipulation intensity
   - Adding more levels/conditions
   - Using within-subjects design
   - Increasing sample size

3. **Effect Sizes**: Use as rough guide, not precise estimates
4. **Sample Responses**: Check for face validity and realism

## Dependencies

- Python 3.11+
- `copilot_workflow.schemas` (internal)
- Standard library: `logging`, `random`, `statistics`, `uuid`

## Version History

- **1.0.0** (2025-01-23): Initial implementation
  - Persona generation with attachment styles and Big Five
  - Response simulation for quantitative and qualitative data
  - Diagnostics engine with dead vars and weak effects detection
  - Integration with Research Copilot workflow

## Contributing

To improve simulation realism:

1. **Add Response Functions**: Implement more sophisticated score generation
2. **Extend Persona Types**: Add clinical populations, age-specific profiles
3. **Improve Text Generation**: Integrate LLMs for more varied responses
4. **Add Validation**: Compare synthetic vs. real data distributions

## License

Part of the Research Copilot project.

## Support

For issues or questions:
- Review workflow documentation in `copilot_workflow/README.md`
- Check test files for usage examples
- See `AGENTS.md` for development guidelines
