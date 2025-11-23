"""Module 4 Main Orchestrator: Stimulus Factory.

Orchestrates:
1. Stimulus generation (scenarios/vignettes)
2. Metadata annotation (valence, intensity, themes)
3. Balance optimization (equal distribution)
4. Content filtering (safety checks)

Input: ProjectState with design from Module 3
Output: ProjectState with balanced, annotated stimuli
"""

import logging
from typing import Dict, Optional, Tuple, List

from copilot_workflow.config import get_config
from copilot_workflow.schemas import (
    ProjectState,
    AuditEntry,
)
from Stimulus_Factory.stimulus_generator import (
    generate_stimuli,
    StimulusGenerationError,
)
from Stimulus_Factory.metadata_annotator import (
    annotate_stimuli,
    get_metadata_summary,
    MetadataAnnotationError,
)
from Stimulus_Factory.balance_optimizer import (
    balance_stimuli_across_conditions,
    calculate_balance_score,
    BalanceOptimizationError,
)
from Stimulus_Factory.content_filter import (
    filter_stimuli,
    get_filter_summary,
)

logger = logging.getLogger(__name__)

config = get_config()


class Module4Error(Exception):
    """Raised when Module 4 execution fails."""
    pass


async def run(
    project: ProjectState,
    num_stimuli_per_condition: int = 10,
    style: str = "scenario",
    relationship_types: Optional[List[str]] = None,
    filter_mode: str = "lenient",
    use_llm: bool = True
) -> ProjectState:
    """Run Module 4: Stimulus Factory.
    
    Args:
        project: Project state with design from Module 3
        num_stimuli_per_condition: Number of stimuli to generate per condition
        style: Generation style (scenario, dialogue, vignette)
        relationship_types: Types of relationships to include
        filter_mode: Content filter mode (lenient, strict)
        use_llm: Whether to use LLM for generation/annotation
        
    Returns:
        Updated ProjectState with stimuli
        
    Raises:
        Module4Error: If any component fails critically
    """
    logger.info("="*60)
    logger.info("MODULE 4: Stimulus Factory")
    logger.info("="*60)
    
    # Validate inputs
    if not project.design:
        error_msg = "No design found. Run Module 3 (Design Builder) first."
        logger.error(error_msg)
        project.audit_log.append(
            AuditEntry(
                level="error",
                message=error_msg,
                location="stimulus_factory"
            )
        )
        raise Module4Error(error_msg)
    
    if not project.design.conditions:
        error_msg = "Design has no conditions. Check Module 3 output."
        logger.error(error_msg)
        raise Module4Error(error_msg)
    
    logger.info(f"Starting stimulus factory with {len(project.design.conditions)} conditions")
    
    # Step 1: Generate stimuli
    logger.info("Step 1/4: Generating stimuli...")
    try:
        stimuli = await generate_stimuli(
            design=project.design,
            num_stimuli_per_condition=num_stimuli_per_condition,
            style=style,
            relationship_types=relationship_types,
            use_llm=use_llm
        )
        
        logger.info(f"Generated {len(stimuli)} stimuli")
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message=f"Generated {len(stimuli)} stimuli",
                location="stimulus_generator",
                details={
                    "total": len(stimuli),
                    "style": style,
                    "per_condition": num_stimuli_per_condition
                }
            )
        )
        
    except StimulusGenerationError as e:
        error_msg = f"Stimulus generation failed: {e}"
        logger.error(error_msg)
        project.audit_log.append(
            AuditEntry(
                level="error",
                message=error_msg,
                location="stimulus_generator"
            )
        )
        raise Module4Error(error_msg)
    
    # Step 2: Annotate with metadata
    logger.info("Step 2/4: Annotating stimuli with metadata...")
    try:
        stimuli = await annotate_stimuli(stimuli, use_llm=use_llm)
        
        # Get metadata summary
        metadata_summary = get_metadata_summary(stimuli)
        
        logger.info(f"Annotated {len(stimuli)} stimuli")
        logger.info(f"Valence distribution: {metadata_summary.get('valence_distribution', {})}")
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message="Annotated stimuli with metadata",
                location="metadata_annotator",
                details=metadata_summary
            )
        )
        
    except MetadataAnnotationError as e:
        logger.warning(f"Metadata annotation failed: {e}")
        # Continue without metadata (non-critical)
        project.audit_log.append(
            AuditEntry(
                level="warning",
                message=f"Metadata annotation failed: {e}",
                location="metadata_annotator"
            )
        )
    
    # Step 3: Balance across conditions
    logger.info("Step 3/4: Balancing stimuli across conditions...")
    try:
        stimuli = balance_stimuli_across_conditions(
            stimuli=stimuli,
            conditions=project.design.conditions,
            target_per_condition=num_stimuli_per_condition
        )
        
        balance_score = calculate_balance_score(stimuli)
        
        logger.info(f"Balanced to {len(stimuli)} stimuli (score: {balance_score:.2f})")
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message=f"Balanced stimuli (score: {balance_score:.2f})",
                location="balance_optimizer",
                details={
                    "final_count": len(stimuli),
                    "balance_score": balance_score
                }
            )
        )
        
    except BalanceOptimizationError as e:
        logger.warning(f"Balance optimization failed: {e}")
        # Continue with unbalanced stimuli (non-critical)
        balance_score = 0.5
        project.audit_log.append(
            AuditEntry(
                level="warning",
                message=f"Balance optimization failed: {e}",
                location="balance_optimizer"
            )
        )
    
    # Step 4: Filter problematic content
    logger.info(f"Step 4/4: Filtering content (mode: {filter_mode})...")
    try:
        strict = (filter_mode == "strict")
        kept_stimuli, flagged_reasons = filter_stimuli(stimuli, strict_mode=strict)
        
        filter_summary = get_filter_summary(flagged_reasons)
        
        logger.info(
            f"Filtered: {len(kept_stimuli)} kept, "
            f"{filter_summary['total_flagged']} flagged"
        )
        
        if filter_summary['total_flagged'] > 0:
            logger.info(f"Flagged reasons: {filter_summary['reasons']}")
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message=f"Content filtering complete",
                location="content_filter",
                details=filter_summary
            )
        )
        
        stimuli = kept_stimuli
        
    except Exception as e:
        logger.warning(f"Content filtering failed: {e}")
        # Continue with unfiltered stimuli (non-critical)
        project.audit_log.append(
            AuditEntry(
                level="warning",
                message=f"Content filtering failed: {e}",
                location="content_filter"
            )
        )
    
    # Update ProjectState with stimuli
    project.stimuli = stimuli
    
    logger.info("="*60)
    logger.info("MODULE 4 COMPLETE")
    logger.info(f"  Total Stimuli: {len(stimuli)}")
    logger.info(f"  Conditions: {len(project.design.conditions)}")
    logger.info(f"  Per Condition: ~{len(stimuli) // len(project.design.conditions)}")
    logger.info(f"  Balance Score: {balance_score:.2f}")
    logger.info("="*60)
    
    return project


async def run_with_summary(
    project: ProjectState,
    num_stimuli_per_condition: int = 10,
    style: str = "scenario",
    relationship_types: Optional[List[str]] = None,
    filter_mode: str = "lenient",
    use_llm: bool = True
) -> Tuple[ProjectState, Dict]:
    """Run Module 4 and return summary dict.
    
    Args:
        project: Project state
        num_stimuli_per_condition: Number of stimuli per condition
        style: Generation style
        relationship_types: Relationship types to include
        filter_mode: Content filter mode
        use_llm: Whether to use LLM
        
    Returns:
        Tuple of (updated_project, summary_dict)
    """
    try:
        result_project = await run(
            project,
            num_stimuli_per_condition=num_stimuli_per_condition,
            style=style,
            relationship_types=relationship_types,
            filter_mode=filter_mode,
            use_llm=use_llm
        )
        
        # Build summary
        metadata_summary = get_metadata_summary(result_project.stimuli) if result_project.stimuli else {}
        balance_score = calculate_balance_score(result_project.stimuli) if result_project.stimuli else 0.0
        
        # Count per condition
        per_condition = {}
        if result_project.stimuli:
            for stimulus in result_project.stimuli:
                cond = stimulus.assigned_condition
                per_condition[cond] = per_condition.get(cond, 0) + 1
        
        summary = {
            "total_stimuli": len(result_project.stimuli) if result_project.stimuli else 0,
            "per_condition": per_condition,
            "balance_score": balance_score,
            "metadata_summary": metadata_summary,
            "audit_entries": len(result_project.audit_log)
        }
        
        return result_project, summary
        
    except Module4Error as e:
        logger.error(f"Module 4 failed: {e}")
        
        # Return original project with error summary
        summary = {
            "total_stimuli": 0,
            "per_condition": {},
            "balance_score": 0.0,
            "metadata_summary": {},
            "audit_entries": len(project.audit_log),
            "error": str(e)
        }
        
        return project, summary
