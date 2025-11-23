"""Diagnostics Engine for Simulation Results.

Computes statistics, identifies problematic variables and weak manipulations,
and provides diagnostic feedback on experimental design quality.
"""

import logging
import statistics
from typing import List, Dict, Any
from collections import defaultdict

from copilot_workflow.schemas import (
    SyntheticParticipant,
    ExperimentDesign,
    SyntheticResponse
)

logger = logging.getLogger(__name__)


class DiagnosticsEngine:
    """Analyzes simulation results for design quality issues."""
    
    # Thresholds for diagnostics
    DEAD_VAR_THRESHOLD = 0.3  # SD below this indicates dead variable
    WEAK_EFFECT_THRESHOLD = 0.3  # Cohen's d below this indicates weak effect
    
    def __init__(self):
        """Initialize the diagnostics engine."""
        logger.info("DiagnosticsEngine initialized")
    
    def compute_diagnostics(
        self,
        participants: List[SyntheticParticipant],
        design: ExperimentDesign
    ) -> Dict[str, Any]:
        """Compute comprehensive diagnostics from simulation results.
        
        Args:
            participants: List of synthetic participants
            design: Experimental design
            
        Returns:
            Dictionary with diagnostics:
                - condition_means: Means and SDs by condition and DV
                - dead_variables: DVs with insufficient variance
                - weak_effects: Condition comparisons with small effect sizes
                - effect_estimates: Estimated effect sizes
        """
        logger.info("Computing simulation diagnostics...")
        
        # Step 1: Aggregate data by condition
        condition_data = self._aggregate_by_condition(participants)
        
        # Step 2: Compute condition means and SDs
        condition_means = self._compute_condition_stats(condition_data, design)
        
        # Step 3: Identify dead variables (low variance)
        dead_variables = self._identify_dead_variables(condition_data)
        
        # Step 4: Detect weak effects (small between-condition differences)
        weak_effects = self._detect_weak_effects(condition_data, condition_means)
        
        # Step 5: Compute effect size estimates
        effect_estimates = self._compute_effect_sizes(condition_data, condition_means)
        
        logger.info(
            f"Diagnostics complete: {len(dead_variables)} dead vars, "
            f"{len(weak_effects)} weak effects"
        )
        
        return {
            "condition_means": condition_means,
            "dead_variables": dead_variables,
            "weak_effects": weak_effects,
            "effect_estimates": effect_estimates
        }
    
    def _aggregate_by_condition(
        self,
        participants: List[SyntheticParticipant]
    ) -> Dict[str, Dict[str, List[float]]]:
        """Aggregate response data by condition and DV.
        
        Args:
            participants: List of synthetic participants
            
        Returns:
            Nested dict: {condition_id: {dv_name: [scores]}}
        """
        condition_data = defaultdict(lambda: defaultdict(list))
        
        for participant in participants:
            for response in participant.responses:
                condition_id = response.condition_id
                for dv_name, score in response.dv_scores.items():
                    condition_data[condition_id][dv_name].append(score)
        
        return dict(condition_data)
    
    def _compute_condition_stats(
        self,
        condition_data: Dict[str, Dict[str, List[float]]],
        design: ExperimentDesign
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Compute means and SDs for each condition and DV.
        
        Args:
            condition_data: Aggregated condition data
            design: Experimental design
            
        Returns:
            Nested dict: {dv_name: {condition_id: {mean, sd, n}}}
        """
        stats = defaultdict(dict)
        
        # Get all DVs from measures
        all_dvs = {measure.label for measure in design.measures}
        
        for condition_id, dv_scores in condition_data.items():
            for dv_name, scores in dv_scores.items():
                if len(scores) > 0:
                    mean = statistics.mean(scores)
                    sd = statistics.stdev(scores) if len(scores) > 1 else 0.0
                    
                    if dv_name not in stats:
                        stats[dv_name] = {}
                    
                    stats[dv_name][condition_id] = {
                        "mean": round(mean, 2),
                        "sd": round(sd, 2),
                        "n": len(scores)
                    }
        
        return dict(stats)
    
    def _identify_dead_variables(
        self,
        condition_data: Dict[str, Dict[str, List[float]]]
    ) -> List[str]:
        """Identify DVs with insufficient variance (dead variables).
        
        Args:
            condition_data: Aggregated condition data
            
        Returns:
            List of DV names with low variance
        """
        dead_vars = []
        
        # Check overall variance across all conditions for each DV
        all_dv_scores = defaultdict(list)
        
        for condition_id, dv_scores in condition_data.items():
            for dv_name, scores in dv_scores.items():
                all_dv_scores[dv_name].extend(scores)
        
        for dv_name, all_scores in all_dv_scores.items():
            if len(all_scores) > 1:
                sd = statistics.stdev(all_scores)
                if sd < self.DEAD_VAR_THRESHOLD:
                    dead_vars.append(dv_name)
                    logger.warning(
                        f"Dead variable detected: {dv_name} (SD={sd:.3f})"
                    )
        
        return dead_vars
    
    def _detect_weak_effects(
        self,
        condition_data: Dict[str, Dict[str, List[float]]],
        condition_means: Dict[str, Dict[str, Dict[str, float]]]
    ) -> List[Dict[str, Any]]:
        """Detect condition comparisons with weak effects.
        
        Args:
            condition_data: Aggregated condition data
            condition_means: Computed condition statistics
            
        Returns:
            List of weak effect descriptions
        """
        weak_effects = []
        
        # For each DV, compare all condition pairs
        for dv_name, cond_stats in condition_means.items():
            conditions = list(cond_stats.keys())
            
            for i in range(len(conditions)):
                for j in range(i + 1, len(conditions)):
                    cond1 = conditions[i]
                    cond2 = conditions[j]
                    
                    # Get scores for both conditions
                    scores1 = condition_data[cond1].get(dv_name, [])
                    scores2 = condition_data[cond2].get(dv_name, [])
                    
                    if len(scores1) > 0 and len(scores2) > 0:
                        # Compute Cohen's d
                        cohens_d = self._compute_cohens_d(scores1, scores2)
                        
                        if abs(cohens_d) < self.WEAK_EFFECT_THRESHOLD:
                            weak_effects.append({
                                "dv": dv_name,
                                "condition1": cond1,
                                "condition2": cond2,
                                "cohens_d": round(cohens_d, 3),
                                "message": f"Weak effect between {cond1} and {cond2} on {dv_name}"
                            })
                            logger.warning(
                                f"Weak effect: {cond1} vs {cond2} on {dv_name} "
                                f"(d={cohens_d:.3f})"
                            )
        
        return weak_effects
    
    def _compute_effect_sizes(
        self,
        condition_data: Dict[str, Dict[str, List[float]]],
        condition_means: Dict[str, Dict[str, Dict[str, float]]]
    ) -> List[Dict[str, Any]]:
        """Compute effect size estimates for all condition comparisons.
        
        Args:
            condition_data: Aggregated condition data
            condition_means: Computed condition statistics
            
        Returns:
            List of effect size estimates
        """
        effect_estimates = []
        
        for dv_name, cond_stats in condition_means.items():
            conditions = list(cond_stats.keys())
            
            for i in range(len(conditions)):
                for j in range(i + 1, len(conditions)):
                    cond1 = conditions[i]
                    cond2 = conditions[j]
                    
                    scores1 = condition_data[cond1].get(dv_name, [])
                    scores2 = condition_data[cond2].get(dv_name, [])
                    
                    if len(scores1) > 0 and len(scores2) > 0:
                        cohens_d = self._compute_cohens_d(scores1, scores2)
                        
                        # Interpret effect size
                        if abs(cohens_d) < 0.2:
                            interpretation = "negligible"
                        elif abs(cohens_d) < 0.5:
                            interpretation = "small"
                        elif abs(cohens_d) < 0.8:
                            interpretation = "medium"
                        else:
                            interpretation = "large"
                        
                        effect_estimates.append({
                            "dv": dv_name,
                            "condition1": cond1,
                            "condition2": cond2,
                            "cohens_d": round(cohens_d, 3),
                            "interpretation": interpretation,
                            "mean_diff": round(
                                cond_stats[cond1]["mean"] - cond_stats[cond2]["mean"],
                                2
                            )
                        })
        
        return effect_estimates
    
    def _compute_cohens_d(
        self,
        scores1: List[float],
        scores2: List[float]
    ) -> float:
        """Compute Cohen's d effect size.
        
        Args:
            scores1: Scores from condition 1
            scores2: Scores from condition 2
            
        Returns:
            Cohen's d effect size
        """
        if len(scores1) < 2 or len(scores2) < 2:
            return 0.0
        
        mean1 = statistics.mean(scores1)
        mean2 = statistics.mean(scores2)
        sd1 = statistics.stdev(scores1)
        sd2 = statistics.stdev(scores2)
        
        # Pooled standard deviation
        n1 = len(scores1)
        n2 = len(scores2)
        pooled_sd = ((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2)
        pooled_sd = pooled_sd ** 0.5
        
        if pooled_sd == 0:
            return 0.0
        
        return (mean1 - mean2) / pooled_sd
