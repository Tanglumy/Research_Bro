#!/usr/bin/env python3
"""Hypothesis Validator: Check hypothesis quality and testability.

Validates:
- Has clear IV and DV
- Variables are operationalizable
- Theoretically grounded
- Testable through empirical research
"""

import logging
from typing import Dict, Any, List

from copilot_workflow.schemas import Hypothesis

logger = logging.getLogger(__name__)


class HypothesisValidationResult:
    """Result of hypothesis validation."""
    
    def __init__(self, hypothesis: Hypothesis):
        self.hypothesis = hypothesis
        self.checks: Dict[str, bool] = {}
        self.warnings: List[str] = []
        self.score: float = 0.0
    
    @property
    def is_valid(self) -> bool:
        """Check if hypothesis passes all critical checks."""
        critical_checks = [
            "has_iv_dv",
            "testable",
            "operationalized"
        ]
        return all(self.checks.get(check, False) for check in critical_checks)
    
    def __repr__(self) -> str:
        return f"<HypothesisValidationResult valid={self.is_valid} score={self.score:.2f}>"


def validate_hypothesis(hypothesis: Hypothesis) -> HypothesisValidationResult:
    """Validate a hypothesis for quality and testability.
    
    Args:
        hypothesis: Hypothesis object to validate
        
    Returns:
        HypothesisValidationResult with checks and score
    """
    result = HypothesisValidationResult(hypothesis)
    
    # Check 1: Has IV and DV
    result.checks["has_iv_dv"] = _check_has_iv_dv(hypothesis, result)
    
    # Check 2: Testable (not too vague or broad)
    result.checks["testable"] = _check_testability(hypothesis, result)
    
    # Check 3: Variables are operationalized (specific enough)
    result.checks["operationalized"] = _check_operationalization(hypothesis, result)
    
    # Check 4: Theoretically grounded
    result.checks["theoretically_grounded"] = _check_theoretical_grounding(hypothesis, result)
    
    # Check 5: Expected direction is specified
    result.checks["has_direction"] = _check_has_direction(hypothesis, result)
    
    # Calculate overall quality score (0.0 - 1.0)
    result.score = _calculate_quality_score(result)
    
    logger.info(f"Hypothesis validation: {result.is_valid}, score={result.score:.2f}")
    
    return result


def validate_hypotheses(hypotheses: List[Hypothesis]) -> List[HypothesisValidationResult]:
    """Validate multiple hypotheses.
    
    Args:
        hypotheses: List of Hypothesis objects
        
    Returns:
        List of HypothesisValidationResult
    """
    results = []
    for i, hyp in enumerate(hypotheses, 1):
        logger.debug(f"Validating hypothesis {i}/{len(hypotheses)}: {hyp.text[:50]}...")
        result = validate_hypothesis(hyp)
        results.append(result)
    
    # Log summary
    valid_count = sum(1 for r in results if r.is_valid)
    avg_score = sum(r.score for r in results) / len(results) if results else 0.0
    logger.info(
        f"Validated {len(hypotheses)} hypotheses: "
        f"{valid_count} valid, avg score={avg_score:.2f}"
    )
    
    return results


def _check_has_iv_dv(hypothesis: Hypothesis, result: HypothesisValidationResult) -> bool:
    """Check if hypothesis has at least one IV and one DV."""
    if not hypothesis.iv or not hypothesis.dv:
        result.warnings.append("Missing IV or DV")
        return False
    
    if len(hypothesis.iv) == 0:
        result.warnings.append("No independent variables specified")
        return False
    
    if len(hypothesis.dv) == 0:
        result.warnings.append("No dependent variables specified")
        return False
    
    return True


def _check_testability(hypothesis: Hypothesis, result: HypothesisValidationResult) -> bool:
    """Check if hypothesis is testable (not too vague or broad).
    
    Heuristics:
    - Text is not too short (< 20 chars) or too long (> 500 chars)
    - Contains specific constructs (not just general terms)
    - IV and DV are distinct
    """
    text = hypothesis.text
    
    # Check length
    if len(text) < 20:
        result.warnings.append("Hypothesis text too short (< 20 chars)")
        return False
    
    if len(text) > 500:
        result.warnings.append("Hypothesis text too long (> 500 chars) - may be too complex")
    
    # Check IV and DV are distinct
    iv_lower = {v.lower() for v in hypothesis.iv}
    dv_lower = {v.lower() for v in hypothesis.dv}
    overlap = iv_lower & dv_lower
    if overlap:
        result.warnings.append(f"IV and DV overlap: {overlap}")
        return False
    
    # Check for vague terms
    vague_terms = ["things", "stuff", "factors", "aspects", "elements"]
    text_lower = text.lower()
    found_vague = [term for term in vague_terms if term in text_lower]
    if found_vague:
        result.warnings.append(f"Contains vague terms: {found_vague}")
    
    return True


def _check_operationalization(hypothesis: Hypothesis, result: HypothesisValidationResult) -> bool:
    """Check if variables are operationalized (specific enough to measure/manipulate).
    
    Heuristics:
    - Variable names are not too generic
    - Variables contain multiple words (more specific)
    """
    all_vars = hypothesis.iv + hypothesis.dv + hypothesis.mediators + hypothesis.moderators
    
    # Check for generic variable names
    generic_terms = ["variable", "factor", "measure", "outcome", "predictor"]
    for var in all_vars:
        var_lower = var.lower()
        if any(term in var_lower for term in generic_terms):
            result.warnings.append(f"Variable '{var}' may be too generic")
            return False
    
    # Check if variables are descriptive (prefer multi-word names)
    single_word_vars = [v for v in all_vars if len(v.split()) == 1]
    if len(single_word_vars) > len(all_vars) * 0.5:  # More than half are single words
        result.warnings.append(
            f"Many single-word variables: {single_word_vars[:3]}... "
            f"Consider more specific operationalizations"
        )
    
    return True


def _check_theoretical_grounding(hypothesis: Hypothesis, result: HypothesisValidationResult) -> bool:
    """Check if hypothesis is theoretically grounded."""
    if not hypothesis.theoretical_basis:
        result.warnings.append("No theoretical basis specified")
        return False
    
    if len(hypothesis.theoretical_basis) == 0:
        result.warnings.append("Theoretical basis is empty")
        return False
    
    # Check if theoretical basis contains meaningful frameworks
    for framework in hypothesis.theoretical_basis:
        if len(framework.strip()) < 3:
            result.warnings.append(f"Theoretical framework too short: '{framework}'")
            return False
    
    return True


def _check_has_direction(hypothesis: Hypothesis, result: HypothesisValidationResult) -> bool:
    """Check if expected direction is specified."""
    if not hypothesis.expected_direction:
        result.warnings.append("Expected direction not specified (recommended but not required)")
        return False
    
    direction = hypothesis.expected_direction.strip()
    if len(direction) < 10:
        result.warnings.append("Expected direction too brief")
        return False
    
    return True


def _calculate_quality_score(result: HypothesisValidationResult) -> float:
    """Calculate overall hypothesis quality score (0.0 - 1.0).
    
    Weighted by importance:
    - has_iv_dv: 0.25 (critical)
    - testable: 0.25 (critical)
    - operationalized: 0.25 (critical)
    - theoretically_grounded: 0.15
    - has_direction: 0.10
    """
    weights = {
        "has_iv_dv": 0.25,
        "testable": 0.25,
        "operationalized": 0.25,
        "theoretically_grounded": 0.15,
        "has_direction": 0.10
    }
    
    score = 0.0
    for check, weight in weights.items():
        if result.checks.get(check, False):
            score += weight
    
    # Penalty for warnings
    warning_penalty = min(0.1, len(result.warnings) * 0.02)
    score = max(0.0, score - warning_penalty)
    
    return score
