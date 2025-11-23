#!/usr/bin/env python3
"""Hypothesis Exporter: Export hypotheses to JSON and human-readable formats.

Supports:
- JSON export with full hypothesis details
- Markdown table export for human review
- Summary statistics
"""

import json
import logging
from typing import List, Dict, Any

from copilot_workflow.schemas import Hypothesis
from .hypothesis_validator import HypothesisValidationResult

logger = logging.getLogger(__name__)


def export_to_json(hypotheses: List[Hypothesis]) -> str:
    """Export hypotheses as JSON string.
    
    Args:
        hypotheses: List of Hypothesis objects
        
    Returns:
        JSON string with all hypothesis details
    """
    data = {
        "count": len(hypotheses),
        "hypotheses": [
            {
                "id": h.id,
                "text": h.text,
                "iv": h.iv,
                "dv": h.dv,
                "mediators": h.mediators,
                "moderators": h.moderators,
                "theoretical_basis": h.theoretical_basis,
                "expected_direction": h.expected_direction
            }
            for h in hypotheses
        ]
    }
    
    return json.dumps(data, indent=2)


def export_to_markdown_table(hypotheses: List[Hypothesis]) -> str:
    """Export hypotheses as markdown table.
    
    Args:
        hypotheses: List of Hypothesis objects
        
    Returns:
        Markdown table string
    """
    if not hypotheses:
        return "No hypotheses to display."
    
    lines = []
    lines.append("## Generated Hypotheses\n")
    lines.append("| # | Hypothesis | IV | DV | Mediators | Moderators | Framework | Direction |")
    lines.append("|---|------------|----|----|-----------|------------|-----------|-----------|")
    
    for i, h in enumerate(hypotheses, 1):
        # Truncate long text for table display
        text = h.text[:80] + "..." if len(h.text) > 80 else h.text
        iv_str = ", ".join(h.iv) if h.iv else "N/A"
        dv_str = ", ".join(h.dv) if h.dv else "N/A"
        med_str = ", ".join(h.mediators) if h.mediators else "None"
        mod_str = ", ".join(h.moderators) if h.moderators else "None"
        framework_str = ", ".join(h.theoretical_basis[:2]) if h.theoretical_basis else "N/A"
        direction = h.expected_direction[:40] + "..." if h.expected_direction and len(h.expected_direction) > 40 else h.expected_direction or "N/A"
        
        lines.append(
            f"| {i} | {text} | {iv_str} | {dv_str} | {med_str} | {mod_str} | {framework_str} | {direction} |"
        )
    
    return "\n".join(lines)


def export_with_validation(
    hypotheses: List[Hypothesis],
    validation_results: List[HypothesisValidationResult]
) -> str:
    """Export hypotheses with validation scores.
    
    Args:
        hypotheses: List of Hypothesis objects
        validation_results: Corresponding validation results
        
    Returns:
        Markdown table with validation scores
    """
    if not hypotheses:
        return "No hypotheses to display."
    
    lines = []
    lines.append("## Hypothesis Validation Summary\n")
    lines.append("| # | Hypothesis | Valid | Quality Score | Warnings |")
    lines.append("|---|------------|-------|---------------|----------|")
    
    for i, (h, result) in enumerate(zip(hypotheses, validation_results), 1):
        text = h.text[:60] + "..." if len(h.text) > 60 else h.text
        valid_icon = "✅" if result.is_valid else "❌"
        score = f"{result.score:.2f}"
        warnings = "; ".join(result.warnings[:2]) if result.warnings else "None"
        
        lines.append(
            f"| {i} | {text} | {valid_icon} | {score} | {warnings} |"
        )
    
    return "\n".join(lines)


def export_summary_stats(
    hypotheses: List[Hypothesis],
    validation_results: List[HypothesisValidationResult] = None
) -> Dict[str, Any]:
    """Generate summary statistics for hypotheses.
    
    Args:
        hypotheses: List of Hypothesis objects
        validation_results: Optional validation results
        
    Returns:
        Dictionary with summary statistics
    """
    stats = {
        "total_hypotheses": len(hypotheses),
        "with_mediators": sum(1 for h in hypotheses if h.mediators),
        "with_moderators": sum(1 for h in hypotheses if h.moderators),
        "with_theoretical_basis": sum(1 for h in hypotheses if h.theoretical_basis),
        "with_direction": sum(1 for h in hypotheses if h.expected_direction),
        "unique_ivs": len({v for h in hypotheses for v in h.iv}),
        "unique_dvs": len({v for h in hypotheses for v in h.dv}),
        "frameworks": list({fw for h in hypotheses for fw in h.theoretical_basis})
    }
    
    if validation_results:
        stats["valid_hypotheses"] = sum(1 for r in validation_results if r.is_valid)
        stats["avg_quality_score"] = (
            sum(r.score for r in validation_results) / len(validation_results)
            if validation_results else 0.0
        )
        stats["total_warnings"] = sum(len(r.warnings) for r in validation_results)
    
    return stats


def generate_hypothesis_report(
    hypotheses: List[Hypothesis],
    validation_results: List[HypothesisValidationResult],
    summary: str
) -> str:
    """Generate comprehensive hypothesis report.
    
    Args:
        hypotheses: List of Hypothesis objects
        validation_results: Validation results
        summary: Generation summary from Gemini
        
    Returns:
        Markdown report string
    """
    lines = []
    lines.append("# Hypothesis Generation Report\n")
    
    # Summary section
    lines.append("## Generation Summary\n")
    lines.append(summary)
    lines.append("\n")
    
    # Statistics
    stats = export_summary_stats(hypotheses, validation_results)
    lines.append("## Statistics\n")
    lines.append(f"- **Total Hypotheses**: {stats['total_hypotheses']}")
    if validation_results:
        lines.append(f"- **Valid Hypotheses**: {stats['valid_hypotheses']}")
        lines.append(f"- **Average Quality Score**: {stats['avg_quality_score']:.2f}")
    lines.append(f"- **Hypotheses with Mediators**: {stats['with_mediators']}")
    lines.append(f"- **Hypotheses with Moderators**: {stats['with_moderators']}")
    lines.append(f"- **Unique IVs**: {stats['unique_ivs']}")
    lines.append(f"- **Unique DVs**: {stats['unique_dvs']}")
    lines.append(f"- **Theoretical Frameworks Used**: {len(stats['frameworks'])}")
    lines.append("\n")
    
    # Validation summary
    if validation_results:
        lines.append(export_with_validation(hypotheses, validation_results))
        lines.append("\n")
    
    # Full hypothesis table
    lines.append(export_to_markdown_table(hypotheses))
    lines.append("\n")
    
    # Detailed hypotheses
    lines.append("## Detailed Hypotheses\n")
    for i, h in enumerate(hypotheses, 1):
        lines.append(f"### Hypothesis {i}\n")
        lines.append(f"**Text**: {h.text}\n")
        lines.append(f"**IV**: {', '.join(h.iv)}\n")
        lines.append(f"**DV**: {', '.join(h.dv)}\n")
        if h.mediators:
            lines.append(f"**Mediators**: {', '.join(h.mediators)}\n")
        if h.moderators:
            lines.append(f"**Moderators**: {', '.join(h.moderators)}\n")
        if h.theoretical_basis:
            lines.append(f"**Theoretical Basis**: {', '.join(h.theoretical_basis)}\n")
        if h.expected_direction:
            lines.append(f"**Expected Direction**: {h.expected_direction}\n")
        lines.append("\n")
    
    return "\n".join(lines)
