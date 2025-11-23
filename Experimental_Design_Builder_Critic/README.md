# Module 3: Experimental Design Builder & Critic

## Overview

Module 3 transforms hypotheses from Module 2 into concrete, validated experimental designs with APA-formatted Methods sections.

**Input**: Hypotheses with IV/DV structure from Module 2  
**Output**: Complete experimental design with confound validation, sample size recommendations, and Methods section

---

## Architecture

### Components

1. **design_proposer.py** (~402 lines)
   - Analyzes hypotheses to determine optimal design type
   - Creates experimental conditions based on IVs
   - Maps DVs to measurement instruments
   - Specifies data collection time points
   - Uses OpenAI for enhanced design proposals

2. **confound_checker.py** (~240 lines)
   - Validates design for common confounds
   - Checks manipulation characteristics (length, tone)
   - Identifies order effects and counterbalancing needs
   - Flags sampling limitations and validity threats

3. **sample_size_calculator.py** (~207 lines)
   - Calculates sample size recommendations
   - Provides estimates for small/medium/large effects
   - Accounts for design type (between/within/mixed)
   - Based on power analysis heuristics (G*Power conventions)

4. **methods_writer.py** (~295 lines)
   - Generates APA 7th edition Methods section
   - Includes: Participants, Design, Materials, Procedure
   - Uses OpenAI for narrative generation
   - Creates human-editable output with placeholders

5. **run.py** (~269 lines)
   - Main orchestrator for Module 3 workflow
   - Coordinates all components
   - Updates ProjectState with design
   - Comprehensive audit logging

---

## Usage

### Basic Usage

```python
import asyncio
from copilot_workflow.schemas import ProjectState
from Experimental_Design_Builder_Critic import run

# project has hypotheses from Module 2
project = await run(project, effect_size="medium")

print(f"Design: {project.design.design_type}")
print(f"Conditions: {len(project.design.conditions)}")
print(f"Sample Size: {project.design.sample_size_plan['total_n']}")
```

### With Constraints

```python
from Experimental_Design_Builder_Critic import run, DesignConstraints

constraints = DesignConstraints(
    online=True,
    max_participants=200,
    sample_type="students"
)

project = await run(project, constraints=constraints, effect_size="medium")
```

### Individual Components

```python
from Experimental_Design_Builder_Critic import (
    propose_design,
    check_confounds,
    calculate_sample_size,
    write_methods_section,
)

# Step 1: Propose design
proposal = await propose_design(project)

# Step 2: Check confounds
warnings = check_confounds(proposal)

# Step 3: Calculate sample size
sample_plan = calculate_sample_size(proposal, effect_size="medium")

# Step 4: Write Methods section
methods = await write_methods_section(proposal, sample_plan, project)
```

---

## Design Types

### Between-Subjects
- Each participant in one condition only
- Random assignment to conditions
- Higher N required (no within-subject variance reduction)
- **Example**: Attachment style (secure vs anxious) → emotion regulation

### Within-Subjects
- Each participant experiences all conditions
- Counterbalancing required to control order effects
- Lower N required (paired comparisons)
- **Example**: Emotion regulation strategy (reappraisal vs suppression) → anxiety

### Mixed Design
- Combination of between and within factors
- Most complex but powerful
- **Example**: Attachment style (between) × Time point (within) → relationship satisfaction

---

## Confound Checks

Module 3 automatically checks for:

### Manipulation Confounds
- ✅ Length differences across conditions
- ✅ Emotional tone imbalances
- ✅ Complexity variations

### Order Effects
- ✅ Carryover between conditions
- ✅ Practice effects with multiple time points
- ✅ Need for counterbalancing

### Sampling Issues
- ✅ Generalizability limitations (e.g., student samples)
- ✅ Clinical sample considerations
- ✅ Selection bias in between-subjects designs

### Validity Threats
- ✅ Demand characteristics (especially online)
- ✅ Missing baseline measures
- ✅ Insufficient outcome measures

---

## Sample Size Recommendations

### Effect Size Conventions (Cohen's d)

| Effect Size | Cohen's d | Example |
|-------------|-----------|-------------------------------|
| Small       | 0.2       | Subtle personality effects    |
| Medium      | 0.5       | Most social psych effects     |
| Large       | 0.8       | Clinical interventions        |

### Sample Size Heuristics (Power = 0.80, α = 0.05)

**Between-Subjects (per condition)**:
- Small effect: ~197 per condition (394 total)
- Medium effect: ~32 per condition (64 total)
- Large effect: ~13 per condition (26 total)

**Within-Subjects (total participants)**:
- Small effect: ~98 participants
- Medium effect: ~16 participants
- Large effect: ~7 participants

**Mixed Design**: Between between-subjects and within-subjects estimates

---

## Methods Section Format

Generated Methods sections follow APA 7th edition:

### Participants
- Sample size and demographics
- Recruitment method
- Compensation
- Inclusion/exclusion criteria
- Condition assignment (for between-subjects)

### Design
- Design type and structure
- Independent variables (IVs)
- Dependent variables (DVs)
- Time points

### Materials
- Manipulation materials (stimuli, scenarios)
- Measurement scales (with reliability info)
- Demographics and controls

### Procedure
- Step-by-step what participants did
- Timing and sequence
- Debriefing

**Note**: Output includes [PLACEHOLDERS] for details to be filled in later (e.g., actual demographics, scale alphas).

---

## Configuration

### Required
- `OPENAI_API_KEY` in `.env` (for LLM-enhanced features)

### Optional
- Design constraints (online/lab, sample type, max N)
- Effect size assumption (default: "medium")
- LLM usage flag (default: True, falls back to templates if unavailable)

---

## Error Handling

Module 3 gracefully handles:

1. **Missing hypotheses**: Clear error message, suggests running Module 2 first
2. **LLM unavailable**: Falls back to template-based generation
3. **Confound checks fail**: Continues with empty warnings
4. **Methods writing fails**: Provides placeholder text

All errors logged to `project.audit_log` for debugging.

---

## Integration

### Input from Module 2
```python
project.hypotheses: List[Hypothesis]
# Each hypothesis has:
# - text: str
# - iv: List[str]
# - dv: List[str]
# - mediators: List[str]
# - moderators: List[str]
```

### Output to Module 4
```python
project.design: ExperimentDesign
# Includes:
# - design_type: str
# - conditions: List[Condition]
# - measures: List[Measure]
# - sample_size_plan: Dict
# - methods_section: str
```

---

## Testing

See `tests/test_module3_functional.py` for:
- End-to-end Module 3 workflow
- Individual component tests
- Edge case handling
- Integration with Modules 1 & 2

---

## Limitations

1. **Sample size**: Heuristics, not formal power analysis (use G*Power for precision)
2. **Confounds**: Rule-based detection (may miss nuanced issues)
3. **Design complexity**: Best for standard 2-3 condition designs
4. **Methods writing**: Requires manual review and editing

---

## Future Enhancements

- [ ] Advanced confound detection using LLM
- [ ] Integration with formal power analysis libraries (statsmodels)
- [ ] Support for factorial designs (2×2, 2×3)
- [ ] Covariates and blocking variables
- [ ] Multi-level/hierarchical designs
- [ ] Bayesian sample size planning

---

## References

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.)
- APA (2020). *Publication Manual of the American Psychological Association* (7th ed.)
- Faul et al. (2007). G*Power 3: A flexible statistical power analysis program
