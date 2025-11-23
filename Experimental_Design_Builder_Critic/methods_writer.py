"""Methods Writer: Generates APA-formatted Methods section from design proposal.

Creates a human-editable Methods section with:
- Participants subsection
- Design subsection
- Materials subsection
- Procedure subsection
"""

import json
import logging
from typing import Optional

from copilot_workflow.config import get_config
from copilot_workflow.schemas import ProjectState, ExperimentDesign
from Experimental_Design_Builder_Critic.design_proposer import DesignProposal
from Experimental_Design_Builder_Critic.sample_size_calculator import SampleSizePlan
from spoon_ai.llm import LLMManager

logger = logging.getLogger(__name__)

config = get_config()

# Check if LLM is available
LLM_AVAILABLE = False
try:
    from spoon_ai.llm import LLMManager
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("LLM not available (spoon_ai.llm import failed)")


class MethodsWriterError(Exception):
    """Raised when Methods section generation fails."""
    pass


def _create_participants_section(
    sample_plan: SampleSizePlan,
    proposal: DesignProposal
) -> str:
    """Create Participants subsection.
    
    Args:
        sample_plan: Sample size recommendations
        proposal: Design proposal
        
    Returns:
        Participants section text
    """
    section = "Participants\n\n"
    
    # Sample description
    section += (
        f"We recruited {sample_plan.total_n} participants "
        f"(M_age = [TO BE FILLED], SD = [TO BE FILLED], "
        f"[X]% female, [Y]% male, [Z]% other/non-binary) "
    )
    
    # Recruitment method (placeholder)
    section += (
        "via [recruitment method: e.g., online platform, university participant pool]. "
    )
    
    # Compensation
    section += "Participants received [compensation details] for their time. "
    
    # Inclusion/exclusion criteria
    section += (
        "\n\nInclusion criteria were: (1) age 18 or older, "
        "(2) fluent in English, and (3) [additional criterion if applicable]. "
        "Exclusion criteria included [specify if applicable, or write 'none']. "
    )
    
    # For between-subjects, mention assignment
    if proposal.design_type == "between_subjects":
        section += (
            f"\n\nParticipants were randomly assigned to one of "
            f"{len(proposal.conditions)} conditions: "
            + ", ".join(f"{c.label} (n = {sample_plan.per_condition_n})" for c in proposal.conditions)
            + "."
        )
    
    return section


def _create_design_section(proposal: DesignProposal) -> str:
    """Create Design subsection.
    
    Args:
        proposal: Design proposal
        
    Returns:
        Design section text
    """
    section = "Design\n\n"
    
    # Design type
    design_readable = proposal.design_type.replace("_", "-")
    section += f"This study employed a {design_readable} design. "
    
    # Independent variables
    if proposal.conditions:
        iv_names = list(set(
            c.label.split(" - ")[0] for c in proposal.conditions
        ))
        section += (
            f"The independent variable{'s' if len(iv_names) > 1 else ''} "
            f"{'were' if len(iv_names) > 1 else 'was'} {', '.join(iv_names)}. "
        )
    
    # Conditions
    section += f"\n\nConditions:\n"
    for i, condition in enumerate(proposal.conditions, 1):
        desc = condition.manipulation_description or "[manipulation details to be specified]"
        section += f"  {i}. {condition.label}: {desc}\n"
    
    # Dependent variables
    if proposal.measures:
        dv_labels = [m.label for m in proposal.measures]
        section += (
            f"\nThe dependent variable{'s' if len(dv_labels) > 1 else ''} "
            f"{'were' if len(dv_labels) > 1 else 'was'} {', '.join(dv_labels)}, "
            f"measured using {', '.join(m.scale for m in proposal.measures)}. "
        )
    
    # Time points
    if len(proposal.time_points) > 1:
        readable_times = [tp.replace("_", " ") for tp in proposal.time_points]
        section += (
            f"\n\nMeasures were collected at {len(proposal.time_points)} time points: "
            + ", ".join(readable_times) + "."
        )
    
    return section


def _create_materials_section(proposal: DesignProposal) -> str:
    """Create Materials subsection.
    
    Args:
        proposal: Design proposal
        
    Returns:
        Materials section text
    """
    section = "Materials\n\n"
    
    # Manipulation materials (if applicable)
    if proposal.conditions and len(proposal.conditions) > 1:
        section += "Manipulation Materials\n\n"
        section += (
            "[Describe stimuli, scenarios, or interventions used in each condition. "
            "Include word count, presentation format, duration, etc.]\n\n"
        )
    
    # Measures
    section += "Measures\n\n"
    for measure in proposal.measures:
        section += f"{measure.label} ({measure.scale})\n"
        section += (
            f"[Describe the scale: number of items, response format (e.g., 1-7 Likert), "
            f"sample items, reliability (Cronbach's alpha), and validity evidence. "
            f"Timing: {', '.join(measure.time_points)}]\n\n"
        )
    
    # Additional measures
    section += (
        "Demographics and Control Variables\n\n"
        "Participants reported their age, gender, and [other relevant demographics]. "
        "[Specify any additional control variables or covariates measured.]\n\n"
    )
    
    return section


def _create_procedure_section(
    proposal: DesignProposal,
    project: ProjectState
) -> str:
    """Create Procedure subsection.
    
    Args:
        proposal: Design proposal
        project: Full project state for context
        
    Returns:
        Procedure section text
    """
    section = "Procedure\n\n"
    
    # General setup
    section += (
        "[Specify setting: online via Qualtrics/Prolific, or in-person lab]. "
        "After providing informed consent, participants completed the study in the following sequence:\n\n"
    )
    
    # Step-by-step procedure based on time points
    for i, time_point in enumerate(proposal.time_points, 1):
        readable_time = time_point.replace("_", " ").title()
        section += f"{i}. {readable_time}\n"
        
        if "baseline" in time_point.lower():
            section += (
                "   Participants completed baseline measures of [list DVs] "
                "and provided demographic information.\n\n"
            )
        elif "manipulation" in time_point.lower():
            section += (
                "   Participants were exposed to the experimental manipulation "
                "[describe briefly: e.g., read a vignette, completed a task]. "
            )
            if proposal.design_type == "within_subjects":
                section += "All participants completed all conditions in counterbalanced order. "
            section += "\n\n"
            
            section += (
                "   Immediately after, participants completed post-manipulation measures "
                "of [list DVs] and manipulation checks.\n\n"
            )
        elif "follow" in time_point.lower():
            section += (
                "   [X days/weeks] later, participants completed follow-up measures "
                "to assess [stability, long-term effects, etc.].\n\n"
            )
    
    # Debriefing
    section += (
        "Upon completion, participants were debriefed about the study's purpose "
        "and thanked for their participation. The entire study took approximately "
        "[X] minutes to complete.\n"
    )
    
    return section


async def _generate_methods_with_llm(
    proposal: DesignProposal,
    sample_plan: SampleSizePlan,
    project: ProjectState
) -> str:
    """Use LLM to generate enhanced Methods section.
    
    Args:
        proposal: Design proposal
        sample_plan: Sample size plan
        project: Full project state
        
    Returns:
        Generated Methods section text
    """
    if not LLM_AVAILABLE:
        raise MethodsWriterError("LLM not available for Methods generation")
    
    if not config.is_provider_available("openai"):
        raise MethodsWriterError("OpenAI not available. Check OPENAI_API_KEY in .env")
    
    # Prepare context
    conditions_text = "\n".join([
        f"  - {c.label}: {c.description}"
        for c in proposal.conditions
    ])
    
    measures_text = "\n".join([
        f"  - {m.label} (measured with {m.scale} at {', '.join(m.time_points)})"
        for m in proposal.measures
    ])
    
    prompt = f"""You are an expert experimental psychologist writing a Methods section for a research paper.

Research Question: {project.rq.raw_text}

Study Design:
- Type: {proposal.design_type}
- Sample size: {sample_plan.total_n} total participants ({sample_plan.per_condition_n} per condition)
- Time points: {', '.join(proposal.time_points)}

Conditions:
{conditions_text}

Measures:
{measures_text}

Task: Write a complete Methods section in APA 7th edition format.

Include these subsections:
1. Participants (who, how recruited, compensation, inclusion/exclusion criteria)
2. Design (IV, DV, design type, counterbalancing if needed)
3. Materials (describe each measure with reliability info, manipulation materials)
4. Procedure (step-by-step what participants did)

Style requirements:
- Professional, objective tone
- Past tense ("Participants completed...")
- Clear and concise
- Include placeholders [IN BRACKETS] for details to be filled in later
- Approximately 500-700 words total

Output only the Methods section text (no title, no extra commentary).
"""
    
    llm_manager = LLMManager()
    
    try:
        response = await llm_manager.chat(
            prompt=prompt,
            provider="openai"
        )
        
        logger.info("Successfully generated Methods section with LLM")
        return response.strip()
        
    except Exception as e:
        logger.error(f"LLM Methods generation failed: {e}")
        raise MethodsWriterError(f"Failed to generate Methods section with LLM: {e}")


async def write_methods_section(
    proposal: DesignProposal,
    sample_plan: SampleSizePlan,
    project: ProjectState,
    use_llm: bool = True
) -> str:
    """Generate Methods section for a design proposal.
    
    Args:
        proposal: Design proposal from design_proposer
        sample_plan: Sample size plan from sample_size_calculator
        project: Full project state for context
        use_llm: If True, use LLM for enhanced writing; if False, use template
        
    Returns:
        APA-formatted Methods section text
        
    Raises:
        MethodsWriterError: If Methods generation fails
    """
    logger.info("Starting Methods section generation")
    
    # Try LLM-enhanced generation first
    if use_llm and LLM_AVAILABLE and config.is_provider_available("openai"):
        try:
            methods_text = await _generate_methods_with_llm(
                proposal, sample_plan, project
            )
            logger.info("Generated Methods section with LLM")
            return methods_text
        except MethodsWriterError as e:
            logger.warning(f"LLM generation failed, using template: {e}")
            # Fall through to template-based generation
    
    # Template-based generation (fallback)
    logger.info("Using template-based Methods generation")
    
    sections = [
        "Method\n" + "="*60 + "\n\n",
        _create_participants_section(sample_plan, proposal),
        "\n\n",
        _create_design_section(proposal),
        "\n\n",
        _create_materials_section(proposal),
        "\n\n",
        _create_procedure_section(proposal, project),
    ]
    
    methods_text = "".join(sections)
    
    logger.info(
        f"Methods section generation complete "
        f"({len(methods_text)} characters, ~{len(methods_text.split())} words)"
    )
    
    return methods_text


def format_methods_for_export(methods_text: str) -> str:
    """Format Methods section for export (with metadata).
    
    Args:
        methods_text: Raw Methods section text
        
    Returns:
        Formatted Methods section with header
    """
    header = (
        "# Methods Section (Draft)\n"
        "Generated by Research Copilot - Module 3\n\n"
        "⚠️  This is a draft. Review and edit before submission.\n"
        "[Placeholders in brackets] need to be filled in with actual data.\n\n"
        + "="*60 + "\n\n"
    )
    
    return header + methods_text
