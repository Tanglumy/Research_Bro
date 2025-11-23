"""Content Filter: Filters problematic content for safety and ethics.

Filters:
- Inappropriate content (violence, explicit material)
- Extreme scenarios (trauma, illegal activities)
- Implausibility (unrealistic situations)
- Cultural sensitivity issues
"""

import logging
import re
from typing import List, Tuple, Optional

from copilot_workflow.schemas import StimulusItem

logger = logging.getLogger(__name__)


class ContentFilterError(Exception):
    pass


# Keyword-based filtering
INAPPROPRIATE_KEYWORDS = [
    "violence", "assault", "abuse", "rape", "murder", "kill", "death",
    "explicit", "sexual", "sex", "porn", "hate", "racist", "suicide"
]

EXTREME_KEYWORDS = [
    "trauma", "ptsd", "overdose", "addict", "illegal", "crime", "emergency"
]

IMPLAUSIBLE_KEYWORDS = [
    "aliens", "supernatural", "magic", "impossible", "unbelievable"
]


def _check_inappropriate_content(text: str, strict: bool) -> Optional[str]:
    text_lower = text.lower()
    
    for keyword in INAPPROPRIATE_KEYWORDS:
        if keyword in text_lower:
            return f"Inappropriate content: '{keyword}'"
    
    return None


def _check_extreme_scenarios(text: str, strict: bool) -> Optional[str]:
    if not strict:
        return None  # Only filter in strict mode
    
    text_lower = text.lower()
    
    for keyword in EXTREME_KEYWORDS:
        if keyword in text_lower:
            return f"Extreme scenario: '{keyword}'"
    
    return None


def _check_implausibility(text: str, strict: bool) -> Optional[str]:
    if not strict:
        return None
    
    text_lower = text.lower()
    
    for keyword in IMPLAUSIBLE_KEYWORDS:
        if keyword in text_lower:
            return f"Implausible scenario: '{keyword}'"
    
    return None


def _check_cultural_sensitivity(text: str, strict: bool) -> Optional[str]:
    # Basic stereotype detection
    stereotype_patterns = [
        r"all .+ are",
        r".+ people are always",
        r"typical .+ behavior"
    ]
    
    text_lower = text.lower()
    
    for pattern in stereotype_patterns:
        if re.search(pattern, text_lower):
            return "Potential stereotype"
    
    return None


def filter_stimuli(
    stimuli: List[StimulusItem],
    strict_mode: bool = False
) -> Tuple[List[StimulusItem], List[Tuple[str, str]]]:
    """Filter stimuli for problematic content.
    
    Args:
        stimuli: List of stimuli to filter
        strict_mode: If True, apply stricter filtering
        
    Returns:
        Tuple of (kept_stimuli, flagged_reasons)
    """
    logger.info(f"Filtering {len(stimuli)} stimuli (strict={strict_mode})")
    
    kept = []
    flagged = []
    
    for stimulus in stimuli:
        text = stimulus.text
        
        # Run all checks
        issue = None
        issue = issue or _check_inappropriate_content(text, strict_mode)
        issue = issue or _check_extreme_scenarios(text, strict_mode)
        issue = issue or _check_implausibility(text, strict_mode)
        issue = issue or _check_cultural_sensitivity(text, strict_mode)
        
        if issue:
            flagged.append((stimulus.id, issue))
            stimulus.flagged_issues.append(issue)
            if strict_mode:
                continue  # Skip in strict mode
        
        kept.append(stimulus)
    
    logger.info(f"Kept {len(kept)} stimuli, flagged {len(flagged)}")
    return kept, flagged


def get_filter_summary(flagged: List[Tuple[str, str]]) -> dict:
    if not flagged:
        return {"total_flagged": 0, "reasons": {}}
    
    reasons = {}
    for _, reason in flagged:
        reasons[reason] = reasons.get(reason, 0) + 1
    
    return {
        "total_flagged": len(flagged),
        "reasons": reasons
    }
