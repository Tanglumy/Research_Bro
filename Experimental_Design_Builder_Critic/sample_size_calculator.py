"""Sample Size Calculator: Provides sample size recommendations based on design and effect size.

Uses heuristics for common effect sizes (small, medium, large) and design types.
Not a replacement for formal power analysis software, but provides reasonable starting points.
"""

import logging
import math
from typing import Dict, Optional
from dataclasses import dataclass

from Experimental_Design_Builder_Critic.design_proposer import DesignProposal

logger = logging.getLogger(__name__)


@dataclass
class SampleSizePlan:
    """Sample size recommendations for a design."""
    design_type: str
    effect_size: str  # "small", "medium", "large"
    power: float
    total_n: int
    per_condition_n: int
    rationale: str
    considerations: list[str]


# Effect size conventions (Cohen's d)
EFFECT_SIZES = {
    "small": 0.2,
    "medium": 0.5,
    "large": 0.8
}

# Heuristic sample sizes for between-subjects t-test (power=0.80, alpha=0.05)
# Based on G*Power calculations
BETWEEN_SUBJECTS_N = {
    "small": 393,   # per condition: ~197
    "medium": 64,   # per condition: 32
    "large": 26     # per condition: 13
}

# Within-subjects designs need fewer participants (correlation ~0.5)
WITHIN_SUBJECTS_MULTIPLIER = 0.5

# Mixed designs (between-within interaction)
MIXED_DESIGN_MULTIPLIER = 0.75


def _calculate_between_subjects_n(
    effect_size: str,
    power: float = 0.80,
    num_conditions: int = 2
) -> int:
    """Calculate sample size for between-subjects design.
    
    Args:
        effect_size: "small", "medium", or "large"
        power: Desired statistical power (default: 0.80)
        num_conditions: Number of experimental conditions
        
    Returns:
        Total sample size needed
    """
    base_n = BETWEEN_SUBJECTS_N.get(effect_size, BETWEEN_SUBJECTS_N["medium"])
    
    # Adjust for power if not 0.80
    if power != 0.80:
        # Simple approximation: higher power needs more participants
        power_adjustment = power / 0.80
        base_n = int(base_n * power_adjustment)
    
    # For >2 conditions, need more participants (ANOVA vs t-test)
    if num_conditions > 2:
        # Heuristic: add 15% per additional condition
        condition_adjustment = 1 + (0.15 * (num_conditions - 2))
        base_n = int(base_n * condition_adjustment)
    
    return base_n


def _calculate_within_subjects_n(
    effect_size: str,
    power: float = 0.80,
    num_conditions: int = 2,
    correlation: float = 0.5
) -> int:
    """Calculate sample size for within-subjects design.
    
    Args:
        effect_size: "small", "medium", or "large"
        power: Desired statistical power
        num_conditions: Number of conditions
        correlation: Expected correlation between measurements (default: 0.5)
        
    Returns:
        Total sample size needed
    """
    # Start with between-subjects estimate
    between_n = _calculate_between_subjects_n(effect_size, power, num_conditions)
    
    # Within-subjects needs fewer due to reduced error variance
    # Adjustment factor depends on correlation
    within_multiplier = math.sqrt(1 - correlation)
    within_n = int(between_n * within_multiplier * WITHIN_SUBJECTS_MULTIPLIER)
    
    # Minimum of 20 for within-subjects
    return max(20, within_n)


def _calculate_mixed_design_n(
    effect_size: str,
    power: float = 0.80,
    num_between_conditions: int = 2,
    num_within_conditions: int = 2
) -> int:
    """Calculate sample size for mixed design.
    
    Args:
        effect_size: "small", "medium", or "large"
        power: Desired statistical power
        num_between_conditions: Number of between-subjects conditions
        num_within_conditions: Number of within-subjects conditions
        
    Returns:
        Total sample size needed
    """
    # Between-subjects component dominates sample size needs
    between_n = _calculate_between_subjects_n(
        effect_size, power, num_between_conditions
    )
    
    # Slight reduction due to within-subjects component
    mixed_n = int(between_n * MIXED_DESIGN_MULTIPLIER)
    
    return max(40, mixed_n)


def calculate_sample_size(
    proposal: DesignProposal,
    effect_size: str = "medium",
    power: float = 0.80
) -> SampleSizePlan:
    """Calculate recommended sample size for a design proposal.
    
    Args:
        proposal: Design proposal from Module 3
        effect_size: Expected effect size ("small", "medium", "large")
        power: Desired statistical power (default: 0.80)
        
    Returns:
        SampleSizePlan with recommendations
    """
    logger.info(
        f"Calculating sample size for {proposal.design_type} "
        f"design with {effect_size} effect"
    )
    
    # Validate inputs
    if effect_size not in EFFECT_SIZES:
        logger.warning(f"Unknown effect size '{effect_size}', using 'medium'")
        effect_size = "medium"
    
    if not (0.5 <= power <= 0.99):
        logger.warning(f"Power {power} out of range, using 0.80")
        power = 0.80
    
    num_conditions = len(proposal.conditions)
    
    # Calculate based on design type
    if proposal.design_type == "between_subjects":
        total_n = _calculate_between_subjects_n(effect_size, power, num_conditions)
        per_condition_n = total_n // num_conditions
        
        rationale = (
            f"For a between-subjects design with {num_conditions} conditions, "
            f"detecting a {effect_size} effect (d={EFFECT_SIZES[effect_size]}) "
            f"with {int(power*100)}% power requires approximately {total_n} total participants."
        )
        
        considerations = [
            f"Each condition should have ~{per_condition_n} participants",
            "Use random assignment to conditions",
            "Account for ~10-15% attrition in recruitment"
        ]
    
    elif proposal.design_type == "within_subjects":
        total_n = _calculate_within_subjects_n(effect_size, power, num_conditions)
        per_condition_n = total_n  # All participants in all conditions
        
        rationale = (
            f"For a within-subjects design with {num_conditions} conditions, "
            f"detecting a {effect_size} effect with {int(power*100)}% power "
            f"requires approximately {total_n} participants."
        )
        
        considerations = [
            f"All {total_n} participants complete all {num_conditions} conditions",
            "Counterbalance condition order to control for sequence effects",
            "Allow sufficient time between conditions to minimize carryover",
            "Account for ~20% attrition in longitudinal designs"
        ]
    
    else:  # mixed design
        total_n = _calculate_mixed_design_n(effect_size, power, num_conditions, 2)
        per_condition_n = total_n // num_conditions
        
        rationale = (
            f"For a mixed design, detecting a {effect_size} effect "
            f"with {int(power*100)}% power requires approximately {total_n} total participants."
        )
        
        considerations = [
            f"Each between-subjects condition: ~{per_condition_n} participants",
            "All participants complete all within-subjects conditions",
            "Counterbalance within-subjects condition order",
            "Account for ~15% attrition"
        ]
    
    # Add general considerations
    considerations.extend([
        f"This assumes a {effect_size} effect size (Cohen's d={EFFECT_SIZES[effect_size]})",
        "If effect is smaller than expected, study will be underpowered",
        "Consider pilot data or meta-analyses to refine effect size estimates",
        "For final power analysis, use G*Power or similar software"
    ])
    
    plan = SampleSizePlan(
        design_type=proposal.design_type,
        effect_size=effect_size,
        power=power,
        total_n=total_n,
        per_condition_n=per_condition_n,
        rationale=rationale,
        considerations=considerations
    )
    
    logger.info(
        f"Sample size calculation complete: {total_n} total participants "
        f"({per_condition_n} per condition)"
    )
    
    return plan


def get_effect_size_recommendations(proposal: DesignProposal) -> Dict[str, SampleSizePlan]:
    """Get sample size recommendations for all three effect sizes.
    
    Args:
        proposal: Design proposal
        
    Returns:
        Dict mapping effect size to sample size plan
    """
    logger.info("Generating sample size recommendations for all effect sizes")
    
    recommendations = {}
    for effect_size in ["small", "medium", "large"]:
        recommendations[effect_size] = calculate_sample_size(
            proposal, effect_size=effect_size
        )
    
    return recommendations


def format_sample_size_report(plans: Dict[str, SampleSizePlan]) -> str:
    """Format sample size plans as human-readable report.
    
    Args:
        plans: Dict of effect size -> SampleSizePlan
        
    Returns:
        Formatted report string
    """
    report_lines = ["📊 Sample Size Recommendations\n"]
    report_lines.append("=" * 60 + "\n\n")
    
    # Summary table
    report_lines.append("Effect Size | Total N | Per Condition\n")
    report_lines.append("-" * 40 + "\n")
    
    for effect_size in ["small", "medium", "large"]:
        if effect_size in plans:
            plan = plans[effect_size]
            report_lines.append(
                f"{effect_size.capitalize():11s} | {plan.total_n:7d} | {plan.per_condition_n:13d}\n"
            )
    
    report_lines.append("\n")
    
    # Detailed recommendation (medium effect)
    if "medium" in plans:
        medium_plan = plans["medium"]
        report_lines.append("💡 Recommended (Medium Effect)\n")
        report_lines.append("-" * 60 + "\n")
        report_lines.append(f"{medium_plan.rationale}\n\n")
        
        report_lines.append("Key Considerations:\n")
        for i, consideration in enumerate(medium_plan.considerations[:5], 1):
            report_lines.append(f"  {i}. {consideration}\n")
    
    return "".join(report_lines)
