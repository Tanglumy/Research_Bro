# Module 2: Hypothesis Generator & Structurer

## Overview

Generates structured, testable hypotheses from literature knowledge graphs produced by Module 1.

**Input**: Research question + concept nodes/edges from Module 1  
**Output**: 3-5 structured hypotheses with IV/DV/mediators/moderators

---

## Features

### 1. Hypothesis Generation
- **Gemini-powered analysis** of knowledge graph
- Identifies potential IV/DV combinations
- Proposes mediators and moderators where justified
- Links to theoretical frameworks from literature
- Generates diverse hypothesis types (direct, mediation, moderation)

### 2. Hypothesis Validation
- Checks for clear IV and DV specification
- Validates testability (not too vague or broad)
- Verifies variables are operationalizable
- Ensures theoretical grounding
- Calculates quality scores (0.0-1.0)

### 3. Export Formats
- **JSON**: Machine-readable with full details
- **Markdown table**: Human-readable summary
- **Full report**: Comprehensive with validation results

---

## Components

### hypothesis_generator.py (369 lines)
**Core generation logic using Gemini AI**

### hypothesis_validator.py (243 lines)
**Quality and testability validation**

### hypothesis_exporter.py (215 lines)
**Export to multiple formats**

### run.py (292 lines)
**Main orchestration and integration**

---

## Usage

```python
import asyncio
from Hypothesis_Generator_Structurer import run_with_summary

# Run Module 2
project, summary = await run_with_summary(project, num_hypotheses=5)

print(f"Generated {summary['hypotheses_generated']} hypotheses")
print(f"Valid: {summary['valid_hypotheses']}")
print(f"Avg quality: {summary['avg_quality_score']:.2f}")
```

---

## Configuration

**Required**: GEMINI_API_KEY in .env

**Default**: 5 hypotheses, 3 retries, 2s delay

---

## Module Statistics

- **Total Lines**: 1,171
- **Files**: 5 (generator, validator, exporter, run, init)
- **Dependencies**: Gemini API, copilot_workflow schemas
