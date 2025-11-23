"""Module 3 Main Orchestrator: Experimental Design Builder & Critic.

Orchestrates all Module 3 components:
1. Design Proposer - propose design type, conditions, measures
2. Confound Checker - validate design and identify issues
3. Sample Size Calculator - recommend sample sizes
4. Methods Writer - generate APA Methods section

Input: ProjectState with hypotheses from Module 2
Output: ProjectState with design, confounds, sample plan, and Methods section
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import asdict

from copilot_workflow.config import get_config
from copilot_workflow.schemas import (
    ProjectState,
    ExperimentDesign,
    AuditEntry,
)
from Experimental_Design_Builder_Critic.design_proposer import (
    propose_design,
    DesignConstraints,
    DesignProposal,
    DesignProposalError,
)
from Experimental_Design_Builder_Critic.confound_checker import (
    check_confounds,
    format_confound_report,
)
from Experimental_Design_Builder_Critic.sample_size_calculator import (
    calculate_sample_size,
    get_effect_size_recommendations,
    format_sample_size_report,
)
from Experimental_Design_Builder_Critic.methods_writer import (
    write_methods_section,
    format_methods_for_export,
    MethodsWriterError,
)

logger = logging.getLogger(__name__)

config = get_config()


class Module3Error(Exception):
    """Raised when Module 3 execution fails."""
    pass


async def run(
    project: ProjectState,
    constraints: Optional[DesignConstraints] = None,
    effect_size: str = "medium",
    use_llm: bool = True
) -> ProjectState:
    """Run Module 3: Experimental Design Builder & Critic.
    
    Args:
        project: Project state with hypotheses from Module 2
        constraints: Optional user constraints for design
        effect_size: Expected effect size for sample size calculation
        use_llm: Whether to use LLM for enhanced generation
        
    Returns:
        Updated ProjectState with design, confounds, sample plan, Methods section
        
    Raises:
        Module3Error: If any component fails critically
    """
    logger.info("="*60)
    logger.info("MODULE 3: Experimental Design Builder & Critic")
    logger.info("="*60)
    
    # Validate inputs
    if not project.hypotheses:
        error_msg = "No hypotheses found. Run Module 2 (Hypothesis Generator) first."
        logger.error(error_msg)
        project.audit_log.append(
            AuditEntry(
                level="error",
                message=error_msg,
                location="design_builder"
            )
        )
        raise Module3Error(error_msg)
    
    logger.info(f"Starting design builder with {len(project.hypotheses)} hypotheses")
    
    # Step 1: Propose design
    logger.info("Step 1/4: Proposing experimental design...")
    try:
        proposal = await propose_design(
            project,
            constraints=constraints,
            use_llm=use_llm
        )
        
        logger.info(
            f"Design proposal complete: {proposal.design_type}, "
            f"{len(proposal.conditions)} conditions, {len(proposal.measures)} measures"
        )
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message=f"Proposed {proposal.design_type} design",
                location="design_proposer",
                details={
                    "conditions": len(proposal.conditions),
                    "measures": len(proposal.measures),
                    "time_points": len(proposal.time_points)
                }
            )
        )
        
    except DesignProposalError as e:
        error_msg = f"Design proposal failed: {e}"
        logger.error(error_msg)
        project.audit_log.append(
            AuditEntry(
                level="error",
                message=error_msg,
                location="design_proposer"
            )
        )
        raise Module3Error(error_msg)
    
    # Step 2: Check confounds
    logger.info("Step 2/4: Checking for confounds and design issues...")
    try:
        confound_warnings = check_confounds(proposal)
        
        high_severity = sum(1 for w in confound_warnings if w.severity == "high")
        medium_severity = sum(1 for w in confound_warnings if w.severity == "medium")
        
        logger.info(
            f"Confound check complete: {len(confound_warnings)} warnings "
            f"(high={high_severity}, medium={medium_severity})"
        )
        
        if high_severity > 0:
            project.audit_log.append(
                AuditEntry(
                    level="warning",
                    message=f"{high_severity} high-priority design issues detected",
                    location="confound_checker",
                    details={
                        "high_severity": high_severity,
                        "medium_severity": medium_severity
                    }
                )
            )
        
    except Exception as e:
        logger.warning(f"Confound checking failed: {e}")
        confound_warnings = []  # Continue with empty warnings
        project.audit_log.append(
            AuditEntry(
                level="warning",
                message=f"Confound checking failed: {e}",
                location="confound_checker"
            )
        )
    
    # Step 3: Calculate sample size
    logger.info(f"Step 3/4: Calculating sample size (effect size: {effect_size})...")
    try:
        sample_plan = calculate_sample_size(
            proposal,
            effect_size=effect_size,
            power=0.80
        )
        
        # Also get recommendations for all effect sizes
        all_recommendations = get_effect_size_recommendations(proposal)
        
        logger.info(
            f"Sample size calculation complete: {sample_plan.total_n} total participants "
            f"({sample_plan.per_condition_n} per condition)"
        )
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message=f"Recommended sample size: {sample_plan.total_n} participants",
                location="sample_size_calculator",
                details={
                    "effect_size": effect_size,
                    "total_n": sample_plan.total_n,
                    "per_condition_n": sample_plan.per_condition_n
                }
            )
        )
        
    except Exception as e:
        error_msg = f"Sample size calculation failed: {e}"
        logger.error(error_msg)
        project.audit_log.append(
            AuditEntry(
                level="error",
                message=error_msg,
                location="sample_size_calculator"
            )
        )
        raise Module3Error(error_msg)
    
    # Step 4: Write Methods section
    logger.info("Step 4/4: Writing Methods section...")
    try:
        methods_text = await write_methods_section(
            proposal,
            sample_plan,
            project,
            use_llm=use_llm
        )
        
        word_count = len(methods_text.split())
        logger.info(f"Methods section complete ({word_count} words)")
        
        project.audit_log.append(
            AuditEntry(
                level="info",
                message=f"Generated Methods section ({word_count} words)",
                location="methods_writer"
            )
        )
        
    except MethodsWriterError as e:
        logger.warning(f"Methods writing failed: {e}")
        methods_text = "[Methods section generation failed. Use template from design proposal.]"
        project.audit_log.append(
            AuditEntry(
                level="warning",
                message=f"Methods writing failed: {e}",
                location="methods_writer"
            )
        )
    
    # Update ProjectState with design
    project.design = ExperimentDesign(
        design_type=proposal.design_type,
        conditions=proposal.conditions,
        measures=proposal.measures,
        sample_size_plan={
            "effect_size": effect_size,
            "total_n": sample_plan.total_n,
            "per_condition_n": sample_plan.per_condition_n,
            "recommendations": {
                size: {"total_n": plan.total_n, "per_condition_n": plan.per_condition_n}
                for size, plan in all_recommendations.items()
            }
        },
        confound_notes=[
            f"[{w.severity.upper()}] {w.confound_type}: {w.description}"
            for w in confound_warnings
        ]
    )
    
    # Store Methods section (using schema field)
    project.design.methods_draft = methods_text
    
    logger.info("="*60)
    logger.info("MODULE 3 COMPLETE")
    logger.info(f"  Design: {proposal.design_type}")
    logger.info(f"  Conditions: {len(proposal.conditions)}")
    logger.info(f"  Measures: {len(proposal.measures)}")
    logger.info(f"  Sample Size: {sample_plan.total_n} total participants")
    logger.info(f"  Confound Warnings: {len(confound_warnings)}")
    logger.info(f"  Methods: {len(methods_text.split())} words")
    logger.info("="*60)
    
    return project


async def run_with_summary(
    project: ProjectState,
    constraints: Optional[DesignConstraints] = None,
    effect_size: str = "medium",
    use_llm: bool = True
) -> Tuple[ProjectState, Dict]:
    """Run Module 3 and return summary dict.
    
    Args:
        project: Project state with hypotheses
        constraints: Optional design constraints
        effect_size: Expected effect size
        use_llm: Whether to use LLM
        
    Returns:
        Tuple of (updated_project, summary_dict)
    """
    try:
        result_project = await run(
            project,
            constraints=constraints,
            effect_size=effect_size,
            use_llm=use_llm
        )
        
        # Build summary
        # Extract sample size (handle both dict and SampleSizePlan Pydantic model)
        sample_size = 0
        if result_project.design and result_project.design.sample_size_plan:
            sp = result_project.design.sample_size_plan
            # Handle dict (before Pydantic conversion)
            if isinstance(sp, dict):
                sample_size = sp.get("total_n", 0)
            # Handle SampleSizePlan Pydantic model (after conversion by ExperimentDesign)
            elif hasattr(sp, "total_n") and sp.total_n is not None:
                sample_size = sp.total_n
            # Legacy format fallback (old schema)
            elif hasattr(sp, "per_condition_range") and sp.per_condition_range:
                sample_size = sum(sp.per_condition_range) if sp.per_condition_range else 0
        
        # Extract methods word count
        methods_words = 0
        if result_project.design:
            if hasattr(result_project.design, "methods_draft") and result_project.design.methods_draft:
                methods_words = len(result_project.design.methods_draft.split())
            elif hasattr(result_project.design, "methods_section") and result_project.design.methods_section:
                methods_words = len(result_project.design.methods_section.split())
        
        summary = {
            "design_type": result_project.design.design_type if result_project.design else None,
            "num_conditions": len(result_project.design.conditions) if result_project.design else 0,
            "num_measures": len(result_project.design.measures) if result_project.design else 0,
            "sample_size": sample_size,
            "confound_warnings": (
                len(result_project.design.confound_notes)
                if result_project.design and result_project.design.confound_notes
                else 0
            ),
            "methods_word_count": methods_words,
            "audit_entries": len(result_project.audit_log)
        }
        
        return result_project, summary
        
    except Module3Error as e:
        logger.error(f"Module 3 failed: {e}")
        
        # Return original project with error summary
        summary = {
            "design_type": None,
            "num_conditions": 0,
            "num_measures": 0,
            "sample_size": 0,
            "confound_warnings": 0,
            "methods_word_count": 0,
            "audit_entries": len(project.audit_log),
            "error": str(e)
        }
        
        return project, summary
