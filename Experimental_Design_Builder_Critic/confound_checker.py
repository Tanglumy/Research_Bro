"""Confound Checker: Validates experimental designs and identifies potential issues.

Checks for:
- Manipulation confounds (length, tone, complexity)
- Order effects and counterbalancing needs
- Sampling limitations
- Internal and external validity threats
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from copilot_workflow.schemas import ExperimentDesign, Condition, Measure
from Experimental_Design_Builder_Critic.design_proposer import DesignProposal

logger = logging.getLogger(__name__)


@dataclass
class ConfoundWarning:
    """Warning about a potential confound or design issue."""
    severity: str  # "high", "medium", "low"
    confound_type: str  # Category of confound
    description: str  # What the issue is
    recommendation: str  # How to address it


def _check_manipulation_confounds(proposal: DesignProposal) -> List[ConfoundWarning]:
    """Check for confounds in experimental manipulations.
    
    Common issues:
    - Conditions differ in length (word count, duration)
    - Conditions differ in emotional tone
    - Conditions differ in complexity
    
    Args:
        proposal: Design proposal to check
        
    Returns:
        List of confound warnings
    """
    warnings = []
    
    # Check if conditions are well-defined
    if not proposal.conditions:
        warnings.append(
            ConfoundWarning(
                severity="high",
                confound_type="missing_conditions",
                description="No experimental conditions defined",
                recommendation="Define at least 2 conditions to test hypotheses"
            )
        )
        return warnings
    
    # Check for vague condition descriptions
    for condition in proposal.conditions:
        desc = condition.manipulation_description or ""
        if not desc or len(desc) < 20:
            warnings.append(
                ConfoundWarning(
                    severity="medium",
                    confound_type="vague_manipulation",
                    description=f"Condition '{condition.label}' has vague or missing manipulation description",
                    recommendation="Provide specific details about what participants do/experience in this condition"
                )
            )
    
    # Check for potential length confounds (heuristic)
    condition_descriptions = [c.manipulation_description or "" for c in proposal.conditions]
    if len(set(len(desc.split()) for desc in condition_descriptions)) > 1:
        word_counts = [len(desc.split()) for desc in condition_descriptions]
        if max(word_counts) > min(word_counts) * 2:  # >2x difference
            warnings.append(
                ConfoundWarning(
                    severity="medium",
                    confound_type="length_confound",
                    description="Condition descriptions vary greatly in length (possible stimulus length confound)",
                    recommendation="Ensure all condition stimuli are approximately equal in length"
                )
            )
    
    # Check for emotional tone keywords
    positive_words = ["happy", "positive", "success", "joy", "excited", "pleasant"]
    negative_words = ["sad", "negative", "failure", "anger", "anxious", "unpleasant"]
    
    tone_detected = []
    for condition in proposal.conditions:
        desc_lower = (condition.manipulation_description or "").lower()
        has_positive = any(word in desc_lower for word in positive_words)
        has_negative = any(word in desc_lower for word in negative_words)
        
        if has_positive and not has_negative:
            tone_detected.append((condition.label, "positive"))
        elif has_negative and not has_positive:
            tone_detected.append((condition.label, "negative"))
    
    if len(tone_detected) > 0 and len(tone_detected) != len(proposal.conditions):
        warnings.append(
            ConfoundWarning(
                severity="high",
                confound_type="tone_confound",
                description="Some conditions have emotional tone (positive/negative) while others don't",
                recommendation="Either control emotional tone across all conditions or measure it as a manipulation check"
            )
        )
    
    logger.info(f"Found {len(warnings)} manipulation confound warnings")
    return warnings


def _check_order_effects(proposal: DesignProposal) -> List[ConfoundWarning]:
    """Check for order effects and counterbalancing needs.
    
    Args:
        proposal: Design proposal to check
        
    Returns:
        List of confound warnings
    """
    warnings = []
    
    # Within-subjects designs need counterbalancing
    if proposal.design_type in ["within_subjects", "mixed"]:
        warnings.append(
            ConfoundWarning(
                severity="high",
                confound_type="order_effects",
                description=f"{proposal.design_type} design requires counterbalancing to avoid order effects",
                recommendation="Randomize condition order across participants or use a Latin square design"
            )
        )
    
    # Check for multiple time points (carryover effects)
    if len(proposal.time_points) > 2:
        warnings.append(
            ConfoundWarning(
                severity="medium",
                confound_type="carryover_effects",
                description=f"Multiple time points ({len(proposal.time_points)}) may have carryover effects",
                recommendation="Allow sufficient time between measurements and assess practice effects"
            )
        )
    
    logger.info(f"Found {len(warnings)} order effect warnings")
    return warnings


def _check_sampling_issues(proposal: DesignProposal) -> List[ConfoundWarning]:
    """Check for potential sampling limitations.
    
    Args:
        proposal: Design proposal to check
        
    Returns:
        List of confound warnings
    """
    warnings = []
    
    # Check for sample representativeness (based on design notes)
    student_keywords = ["student", "undergraduate", "college", "university"]
    clinical_keywords = ["clinical", "patient", "diagnosis", "disorder"]
    
    notes_text = " ".join(proposal.design_notes).lower() if proposal.design_notes else ""
    
    if any(word in notes_text for word in student_keywords):
        warnings.append(
            ConfoundWarning(
                severity="low",
                confound_type="sampling_limitation",
                description="Student samples may limit generalizability",
                recommendation="Discuss generalizability limitations in paper; consider replication with community samples"
            )
        )
    
    if any(word in notes_text for word in clinical_keywords):
        warnings.append(
            ConfoundWarning(
                severity="medium",
                confound_type="sampling_limitation",
                description="Clinical samples may have unique characteristics affecting results",
                recommendation="Include comparison with non-clinical controls; report clinical characteristics"
            )
        )
    
    logger.info(f"Found {len(warnings)} sampling issue warnings")
    return warnings


def _check_validity_threats(proposal: DesignProposal) -> List[ConfoundWarning]:
    """Check for common internal and external validity threats.
    
    Args:
        proposal: Design proposal to check
        
    Returns:
        List of confound warnings
    """
    warnings = []
    
    # Check for demand characteristics (online designs)
    rationale_lower = proposal.rationale.lower()
    if "online" in rationale_lower:
        warnings.append(
            ConfoundWarning(
                severity="medium",
                confound_type="demand_characteristics",
                description="Online designs may have demand characteristics and attention issues",
                recommendation="Include attention checks and measure social desirability"
            )
        )
    
    # Check for missing baseline measures
    has_baseline = "baseline" in proposal.time_points
    if not has_baseline:
        warnings.append(
            ConfoundWarning(
                severity="medium",
                confound_type="missing_baseline",
                description="No baseline measurement specified",
                recommendation="Add baseline measures to control for pre-existing differences"
            )
        )
    
    # Check for insufficient measures
    if len(proposal.measures) < 2:
        warnings.append(
            ConfoundWarning(
                severity="low",
                confound_type="limited_measures",
                description="Only one measure specified - limits construct validity",
                recommendation="Consider adding a second measure of the DV or manipulation checks"
            )
        )
    
    # Check for between-subjects with potential selection bias
    if proposal.design_type == "between_subjects":
        warnings.append(
            ConfoundWarning(
                severity="low",
                confound_type="selection_bias",
                description="Between-subjects design requires random assignment to control for selection bias",
                recommendation="Ensure random assignment to conditions and report any group differences at baseline"
            )
        )
    
    logger.info(f"Found {len(warnings)} validity threat warnings")
    return warnings


def check_confounds(proposal: DesignProposal) -> List[ConfoundWarning]:
    """Run all confound checks on a design proposal.
    
    Args:
        proposal: Design proposal to validate
        
    Returns:
        List of all confound warnings, sorted by severity
    """
    logger.info("Starting confound checks")
    
    all_warnings = []
    
    # Run all check functions
    all_warnings.extend(_check_manipulation_confounds(proposal))
    all_warnings.extend(_check_order_effects(proposal))
    all_warnings.extend(_check_sampling_issues(proposal))
    all_warnings.extend(_check_validity_threats(proposal))
    
    # Sort by severity (high -> medium -> low)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_warnings.sort(key=lambda w: severity_order[w.severity])
    
    logger.info(
        f"Confound check complete: {len(all_warnings)} warnings "
        f"(high={sum(1 for w in all_warnings if w.severity == 'high')}, "
        f"medium={sum(1 for w in all_warnings if w.severity == 'medium')}, "
        f"low={sum(1 for w in all_warnings if w.severity == 'low')})"
    )
    
    return all_warnings


def format_confound_report(warnings: List[ConfoundWarning]) -> str:
    """Format confound warnings as human-readable report.
    
    Args:
        warnings: List of confound warnings
        
    Returns:
        Formatted report string
    """
    if not warnings:
        return "✅ No major confounds detected.\n\nThe design appears sound from a validity perspective."
    
    report_lines = ["⚠️  Design Validation Report\n"]
    report_lines.append("="*60 + "\n")
    
    # Group by severity
    for severity in ["high", "medium", "low"]:
        severity_warnings = [w for w in warnings if w.severity == severity]
        if not severity_warnings:
            continue
        
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[severity]
        report_lines.append(f"\n{icon} {severity.upper()} Priority ({len(severity_warnings)} issues)\n")
        report_lines.append("-"*60 + "\n")
        
        for i, warning in enumerate(severity_warnings, 1):
            report_lines.append(f"{i}. {warning.confound_type}\n")
            report_lines.append(f"   Issue: {warning.description}\n")
            report_lines.append(f"   Fix: {warning.recommendation}\n\n")
    
    return "".join(report_lines)
