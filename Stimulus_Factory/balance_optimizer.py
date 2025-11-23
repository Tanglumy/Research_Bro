"""Balance Optimizer: Ensures balanced distribution of stimuli across conditions."""

import logging
import random
from typing import List, Dict, Optional
from collections import Counter

from copilot_workflow.schemas import StimulusItem, Condition

logger = logging.getLogger(__name__)


class BalanceOptimizationError(Exception):
    pass


def _calculate_distribution_metrics(stimuli: List[StimulusItem]) -> Dict:
    if not stimuli:
        return {}
    
    by_condition = {}
    for s in stimuli:
        cond_id = getattr(s.metadata, "assigned_condition", None) if s.metadata else None
        if not cond_id:
            continue
        if cond_id not in by_condition:
            by_condition[cond_id] = []
        by_condition[cond_id].append(s)
    
    valence = Counter()
    intensity = Counter()
    
    for s in stimuli:
        if s.metadata:
            valence[s.metadata.valence] += 1
            intensity[s.metadata.intensity] += 1
    
    return {
        "per_condition": {k: len(v) for k, v in by_condition.items()},
        "valence_distribution": dict(valence),
        "intensity_distribution": dict(intensity),
        "total_stimuli": len(stimuli)
    }


def _select_diverse_subset(stimuli: List[StimulusItem], n: int) -> List[StimulusItem]:
    if len(stimuli) <= n:
        return stimuli
    
    by_valence = {"positive": [], "negative": [], "neutral": [], "mixed": []}
    for s in stimuli:
        if s.metadata:
            by_valence[s.metadata.valence].append(s)
    
    selected = []
    valences = [k for k, v in by_valence.items() if v]
    per_valence = n // len(valences) if valences else n
    
    for valence, items in by_valence.items():
        if items:
            count = min(per_valence, len(items))
            selected.extend(random.sample(items, count))
    
    if len(selected) < n:
        remaining = [s for s in stimuli if s not in selected]
        needed = n - len(selected)
        if remaining:
            selected.extend(random.sample(remaining, min(needed, len(remaining))))
    
    return selected[:n]


def balance_stimuli_across_conditions(
    stimuli: List[StimulusItem],
    conditions: List[Condition],
    target_per_condition: Optional[int] = None
) -> List[StimulusItem]:
    logger.info(f"Balancing {len(stimuli)} stimuli across {len(conditions)} conditions")
    
    if not stimuli:
        raise BalanceOptimizationError("No stimuli to balance")
    
    by_condition = {}
    for s in stimuli:
        cond_id = getattr(s.metadata, "assigned_condition", None) if s.metadata else None
        if not cond_id:
            continue
        if cond_id not in by_condition:
            by_condition[cond_id] = []
        by_condition[cond_id].append(s)
    
    if target_per_condition is None:
        counts = [len(v) for v in by_condition.values()]
        target_per_condition = sorted(counts)[len(counts) // 2] if counts else 10
    
    balanced = []
    for condition, cond_stimuli in by_condition.items():
        if len(cond_stimuli) <= target_per_condition:
            balanced.extend(cond_stimuli)
        else:
            selected = _select_diverse_subset(cond_stimuli, target_per_condition)
            balanced.extend(selected)
    
    logger.info(f"Balanced to {len(balanced)} stimuli ({target_per_condition} per condition)")
    return balanced


def calculate_balance_score(stimuli: List[StimulusItem]) -> float:
    if not stimuli:
        return 0.0
    
    metrics = _calculate_distribution_metrics(stimuli)
    per_condition = metrics.get("per_condition", {})
    
    if not per_condition:
        return 0.0
    
    counts = list(per_condition.values())
    avg_count = sum(counts) / len(counts)
    max_deviation = max(abs(c - avg_count) / avg_count for c in counts if avg_count > 0)
    
    score = 1.0 - max_deviation
    return max(0.0, min(1.0, score))
