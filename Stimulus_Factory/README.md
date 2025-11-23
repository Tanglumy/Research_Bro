# Module 4: Stimulus Factory

## Overview

Module 4 generates balanced, annotated experimental stimuli (scenarios, vignettes, dialogues) with systematic variation across experimental conditions.

**Input**: Experimental design from Module 3  
**Output**: Balanced stimulus sets with metadata

---

## Architecture

### Components (1,161 lines)

1. **stimulus_generator.py** (415 lines)
   - Generates diverse scenarios/vignettes using OpenAI
   - Template fallback for offline use
   - Systematic variation across conditions

2. **metadata_annotator.py** (133 lines)
   - Automatic labeling with 6 dimensions
   - Valence (positive/negative/neutral/mixed)
   - Intensity (low/medium/high)
   - Relationship type (romantic/friend/family/work)
   - Emotional themes (anxiety, conflict, support, etc.)
   - Ambiguity level (low/medium/high)
   - Length metrics (word count, reading time)

3. **balance_optimizer.py** (117 lines)
   - Ensures equal distribution across conditions (±10%)
   - Balances valence and intensity distributions
   - Calculates balance quality score (0-1)

4. **content_filter.py** (142 lines)
   - Filters problematic content (violence, explicit material)
   - Lenient/strict modes for different populations
   - Flags issues with detailed reasons

5. **run.py** (321 lines)
   - Orchestrates all components
   - Updates ProjectState with stimuli
   - Comprehensive audit logging

---

## Usage

### Basic Usage

```python
import asyncio
from copilot_workflow.schemas import ProjectState
from Stimulus_Factory import run

# project.design populated by Module 3
project = await run(
    project,
    num_stimuli_per_condition=10,
    style="scenario",
    filter_mode="lenient",
    use_llm=True
)

print(f"Generated {len(project.stimuli)} stimuli")
```

### With Custom Parameters

```python
from Stimulus_Factory import run

project = await run(
    project,
    num_stimuli_per_condition=15,
    style="vignette",  # or "scenario", "dialogue"
    relationship_types=["romantic", "friend"],
    filter_mode="strict",  # or "lenient"
    use_llm=True
)
```

### Individual Components

```python
from Stimulus_Factory import (
    generate_stimuli,
    annotate_stimuli,
    balance_stimuli_across_conditions,
    filter_stimuli,
)

# Step 1: Generate
stimuli = await generate_stimuli(
    design=project.design,
    num_stimuli_per_condition=10,
    style="scenario"
)

# Step 2: Annotate
stimuli = await annotate_stimuli(stimuli, use_llm=True)

# Step 3: Balance
stimuli = balance_stimuli_across_conditions(
    stimuli,
    conditions=project.design.conditions,
    target_per_condition=10
)

# Step 4: Filter
kept, flagged = filter_stimuli(stimuli, strict_mode=False)
```

---

## Generation Styles

### Scenario (Default)
**Format**: 2-3 sentences describing a situation

**Example**:
```
Your partner hasn't replied to your texts for several hours. 
You know they're busy at work today, but you're starting to 
feel anxious about why they haven't responded.
```

### Vignette
**Format**: 4-5 sentences with rich context and emotional depth

**Example**:
```
It's been a long week, and you've been looking forward to 
spending quality time with your partner this weekend. When 
Friday evening arrives, they mention they made plans with 
friends instead without asking you first. You feel a mix of 
disappointment and hurt, unsure how to express your feelings.
```

### Dialogue
**Format**: 4-6 exchanges between characters

**Example**:
```
You: "I thought we had plans this weekend?"
Partner: "Oh, I forgot to mention - I'm meeting up with friends."
You: "You didn't think to ask me first?"
Partner: "I didn't realize it was a big deal."
```

---

## Metadata Annotation

Each stimulus is automatically labeled with:

### Valence
- **Positive**: Happy, supportive, celebratory situations
- **Negative**: Conflict, disappointment, anxiety
- **Neutral**: Everyday, matter-of-fact situations
- **Mixed**: Bittersweet or ambivalent situations

### Intensity
- **Low**: Subtle, mild emotional situations
- **Medium**: Moderate emotional impact
- **High**: Strong, intense emotional situations

### Relationship Type
- **Romantic**: Partners, dating relationships
- **Friend**: Friendships, social connections
- **Family**: Parents, siblings, relatives
- **Work**: Colleagues, supervisors, workplace
- **Other**: General or ambiguous relationships

### Emotional Themes
- Anxiety, conflict, support, betrayal, disappointment
- Insecurity, jealousy, guilt, rejection, validation
- Multiple themes can be present

### Ambiguity Level
- **Low**: Clear emotional indicators
- **Medium**: Some uncertainty or questions
- **High**: Very ambiguous, open to interpretation

### Length Metrics
- Word count
- Estimated reading time (seconds)

---

## Balance Optimization

### Target Distributions

**Per Condition**:
- Equal count (±10% deviation)
- Example: 10 stimuli per condition for 3 conditions = 30 total

**Valence Distribution**:
- Mix of positive, negative, neutral
- Ideally 30-40% negative, 20-30% positive, 30-40% neutral/mixed

**Intensity Distribution**:
- Mix of low, medium, high
- Ideally 20-30% each intensity level

**Balance Score**:
- 0.0 to 1.0 (higher is better)
- ≥0.80: Good balance
- 0.60-0.79: Acceptable
- <0.60: Significant imbalances

### Rebalancing Strategy

1. **Overgeneration**: Generate 15 per condition, select best 10
2. **Diverse Selection**: Ensure mix of valences and intensities
3. **Length Normalization**: Avoid extreme length differences

---

## Content Filtering

### Lenient Mode (Default)
**Filters**:
- Explicit violence, sexual content
- Hate speech, discrimination
- Self-harm references

**Allows**:
- Realistic conflict scenarios
- Emotional distress (anxiety, sadness)
- Mild relationship problems

**Use For**: Adult populations, emotion regulation studies

### Strict Mode
**Additional Filters**:
- Traumatic events
- Substance abuse
- Extreme scenarios
- Stereotypes

**Use For**: Sensitive populations, clinical samples, children

### Flagged Items

Flagged items are **kept** but marked with `flagged_issues`:
```python
stimulus.flagged_issues = ["Extreme scenario: 'trauma'"]
```

In **strict mode**, flagged items are **removed**.

---

## Example Output

### Input (from Module 3)
```python
design = ExperimentDesign(
    design_type="between_subjects",
    conditions=[
        Condition(id="c1", label="Attachment Anxiety - Low"),
        Condition(id="c2", label="Attachment Anxiety - High")
    ],
    measures=[Measure(label="Emotion Regulation", scale="ERQ")]
)
```

### Output (Module 4)
```python
stimuli = [
    StimulusItem(
        id="stim_001",
        text="Your partner forgot your anniversary. You feel hurt...",
        assigned_condition="c2",  # High anxiety
        metadata=StimulusMetadata(
            valence="negative",
            intensity="medium",
            relationship_type="romantic",
            emotional_themes=["disappointment", "insecurity"],
            ambiguity_level="low",
            word_count=42,
            reading_time_seconds=10
        ),
        flagged_issues=[]
    ),
    # ... 19 more stimuli (10 per condition)
]

# Balance Report
{
    "total_stimuli": 20,
    "per_condition": {"c1": 10, "c2": 10},
    "balance_score": 0.95,
    "metadata_summary": {
        "valence_distribution": {"positive": 4, "negative": 11, "neutral": 5},
        "intensity_distribution": {"low": 5, "medium": 10, "high": 5},
        "relationship_distribution": {"romantic": 12, "friend": 5, "work": 3}
    }
}
```

---

## Configuration

### Required
- `OPENAI_API_KEY` in `.env` (for LLM-powered generation/annotation)

### Optional Parameters
- `num_stimuli_per_condition`: Default 10
- `style`: Default "scenario" (also: "vignette", "dialogue")
- `relationship_types`: Default ["romantic", "friend", "family", "work"]
- `filter_mode`: Default "lenient" (also: "strict")
- `use_llm`: Default True (falls back to templates if False)

---

## Error Handling

Module 4 gracefully handles:

1. **Missing design**: Clear error, suggests running Module 3
2. **LLM unavailable**: Falls back to template-based generation
3. **Annotation fails**: Continues with heuristic-based metadata
4. **Balance fails**: Continues with unbalanced stimuli (logs warning)
5. **Filter fails**: Continues with unfiltered stimuli (logs warning)

All errors logged to `project.audit_log`.

---

## Integration

### Input from Module 3
```python
project.design: ExperimentDesign
# Includes:
# - design_type: str
# - conditions: List[Condition]
# - measures: List[Measure]
```

### Output to Module 5
```python
project.stimuli: List[StimulusItem]
# Each stimulus has:
# - text: str (scenario content)
# - assigned_condition: str (which condition)
# - metadata: StimulusMetadata (valence, intensity, etc.)
# - flagged_issues: List[str] (content warnings)
```

---

## Testing

See `tests/test_module4_functional.py` for:
- Stimulus generation tests
- Metadata annotation validation
- Balance optimization checks
- Content filtering scenarios
- End-to-end Module 4 workflow

---

## Limitations

1. **Generation Quality**: Depends on LLM; templates are basic
2. **Metadata Accuracy**: Heuristics may miss nuances (LLM more accurate)
3. **Cultural Context**: Limited to English, Western relationship norms
4. **Filter Coverage**: Rule-based; may miss subtle issues

---

## Future Enhancements

- [ ] Multi-language support (Spanish, Chinese, etc.)
- [ ] Advanced LLM-based content filtering
- [ ] Stimulus variants for manipulation checks
- [ ] Semantic similarity clustering
- [ ] Participant-facing stimulus presentation format
- [ ] Integration with survey platforms (Qualtrics, REDCap)

---

## References

- Stimulus generation methodology inspired by vignette research (Aguinis & Bradley, 2014)
- Metadata dimensions based on affective science literature (Russell, 2003)
- Content filtering follows APA ethical guidelines for research
