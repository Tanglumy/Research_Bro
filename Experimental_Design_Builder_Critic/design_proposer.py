"""Design Proposer: Core Module 3 component for proposing experimental designs.

Analyzes hypotheses from Module 2 and proposes:
- Design type (between/within/mixed)
- Experimental conditions based on IV manipulations
- Measurement instruments for DVs
- Time points for data collection
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from copilot_workflow.config import get_config
from copilot_workflow.schemas import (
    ProjectState,
    Hypothesis,
    Condition,
    Measure,
    AuditEntry,
)
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


@dataclass
class DesignConstraints:
    """User-specified constraints for experimental design."""
    online: bool = True
    lab_resources: List[str] = field(default_factory=list)
    max_participants: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    sample_type: str = "general_population"  # or "students", "clinical", etc.


@dataclass
class DesignProposal:
    """Proposed experimental design structure."""
    design_type: str  # "between_subjects", "within_subjects", "mixed"
    conditions: List[Condition]
    measures: List[Measure]
    time_points: List[str]  # e.g., ["baseline", "post_manipulation", "follow_up"]
    rationale: str
    design_notes: List[str] = field(default_factory=list)


class DesignProposalError(Exception):
    """Raised when design proposal fails."""
    pass


def _determine_design_type(hypotheses: List[Hypothesis]) -> str:
    """Determine optimal design type based on hypotheses.
    
    Heuristics:
    - If all IVs are trait-like (e.g., attachment style): between_subjects
    - If IVs involve repeated exposures: within_subjects
    - If mix of trait and manipulated IVs: mixed
    
    Args:
        hypotheses: List of hypotheses to analyze
        
    Returns:
        Design type string
    """
    # Keywords suggesting trait-like variables (between-subjects)
    trait_keywords = [
        "attachment", "personality", "trait", "individual differences",
        "gender", "age", "culture", "clinical", "diagnosis"
    ]
    
    # Keywords suggesting manipulable variables (within-subjects possible)
    manipulation_keywords = [
        "condition", "manipulation", "exposure", "intervention",
        "training", "priming", "feedback", "task"
    ]
    
    trait_count = 0
    manipulation_count = 0
    
    for hypothesis in hypotheses:
        for iv in hypothesis.iv:
            iv_lower = iv.lower()
            
            if any(keyword in iv_lower for keyword in trait_keywords):
                trait_count += 1
            elif any(keyword in iv_lower for keyword in manipulation_keywords):
                manipulation_count += 1
            else:
                # Default: assume trait-like for safety (avoid carryover effects)
                trait_count += 1
    
    # Decision logic
    if trait_count > 0 and manipulation_count == 0:
        return "between_subjects"
    elif trait_count == 0 and manipulation_count > 0:
        return "within_subjects"
    else:
        return "mixed"


def _create_conditions(hypotheses: List[Hypothesis]) -> List[Condition]:
    """Create experimental conditions from hypothesis IVs.
    
    Args:
        hypotheses: List of hypotheses with IVs
        
    Returns:
        List of Condition objects
    """
    conditions = []
    
    # Extract unique IVs across all hypotheses
    all_ivs = set()
    for hypothesis in hypotheses:
        all_ivs.update(hypothesis.iv)
    
    # For each IV, create conditions (typically 2-3 levels)
    condition_id = 1
    for iv in sorted(all_ivs):
        # Heuristic: create 2 conditions (low/control vs high/experimental)
        conditions.append(
            Condition(
                id=f"cond_{condition_id:02d}",
                label=f"{iv} - Control",
                manipulation_description=f"Low or baseline level of {iv}"
            )
        )
        condition_id += 1
        
        conditions.append(
            Condition(
                id=f"cond_{condition_id:02d}",
                label=f"{iv} - Experimental",
                manipulation_description=f"High or manipulated level of {iv}"
            )
        )
        condition_id += 1
    
    # If no IVs (edge case), create a single observation condition
    if not conditions:
        conditions.append(
            Condition(
                id="cond_01",
                label="Observation",
                description="Observational study with no manipulation"
            )
        )
    
    logger.info(f"Created {len(conditions)} conditions from {len(all_ivs)} IVs")
    return conditions


def _map_dvs_to_measures(hypotheses: List[Hypothesis], concepts: Dict) -> List[Measure]:
    """Map DVs from hypotheses to measurement instruments.
    
    Args:
        hypotheses: List of hypotheses with DVs
        concepts: Knowledge graph concepts (from Module 1) with measure info
        
    Returns:
        List of Measure objects
    """
    measures = []
    measure_id = 1
    
    # Extract unique DVs
    all_dvs = set()
    for hypothesis in hypotheses:
        all_dvs.update(hypothesis.dv)
    
    # For each DV, try to find a measure from concepts, else create generic
    for dv in sorted(all_dvs):
        # Try to find measure from concept graph
        measure_name = "Self-report scale"  # Default
        
        # Search concepts for this DV
        if concepts and "nodes" in concepts:
            for node in concepts["nodes"]:
                if node.label.lower() in dv.lower() or dv.lower() in node.label.lower():
                    if node.common_measures:
                        measure_name = node.common_measures[0]
                        break
        
        measures.append(
            Measure(
                id=f"measure_{measure_id:02d}",
                label=dv,
                scale=measure_name,
                time_points=["post_manipulation"]  # Default
            )
        )
        measure_id += 1
    
    # If no DVs (edge case), create a placeholder
    if not measures:
        measures.append(
            Measure(
                id="measure_01",
                label="Primary outcome",
                scale="To be determined",
                time_points=["post_manipulation"]
            )
        )
    
    logger.info(f"Created {len(measures)} measures for {len(all_dvs)} DVs")
    return measures


def _determine_time_points(hypotheses: List[Hypothesis]) -> List[str]:
    """Determine measurement time points based on hypothesis structure.
    
    Args:
        hypotheses: List of hypotheses
        
    Returns:
        List of time point labels
    """
    # Default time points
    time_points = ["baseline", "post_manipulation"]
    
    # Add follow-up if mediators/moderators present (longitudinal design)
    for hypothesis in hypotheses:
        if hypothesis.mediators or hypothesis.moderators:
            if "follow_up" not in time_points:
                time_points.append("follow_up")
            break
    
    logger.info(f"Determined {len(time_points)} time points: {time_points}")
    return time_points


async def _generate_design_with_llm(
    hypotheses: List[Hypothesis],
    design_type: str,
    constraints: Optional[DesignConstraints],
    project: ProjectState
) -> Dict:
    """Use LLM to generate detailed design proposal.
    
    Args:
        hypotheses: List of hypotheses
        design_type: Proposed design type
        constraints: User constraints (optional)
        project: Full project state for context
        
    Returns:
        Dict with design details
    """
    if not LLM_AVAILABLE:
        raise DesignProposalError("LLM not available for design generation")
    
    if not config.is_provider_available("openai"):
        raise DesignProposalError("OpenAI not available. Check OPENAI_API_KEY in .env")
    
    # Prepare context
    hypothesis_texts = "\n".join([
        f"- H{i+1}: {h.text} (IV: {', '.join(h.iv)}, DV: {', '.join(h.dv)})"
        for i, h in enumerate(hypotheses[:5])  # Limit to 5 for token efficiency
    ])
    
    constraint_text = ""
    if constraints:
        constraint_text = f"""
        Constraints:
        - Setting: {'Online' if constraints.online else 'Lab'}
        - Max participants: {constraints.max_participants or 'No limit'}
        - Sample type: {constraints.sample_type}
        """
    
    prompt = f"""You are an expert experimental psychologist designing a study.

    Research Question: {project.rq.raw_text}

    Hypotheses:
    {hypothesis_texts}

    Proposed Design Type: {design_type}
    {constraint_text}

    Task: Provide a detailed experimental design proposal.

    Output as JSON with this structure:
    {{
      "design_type": "{design_type}",
      "rationale": "2-3 sentences explaining why this design is optimal",
      "conditions": [
        {{
          "label": "Condition name",
          "description": "What participants do in this condition",
          "manipulation": "Specific manipulation or grouping criterion"
        }}
      ],
      "measures": [
        {{
          "dv_name": "DV from hypothesis",
          "scale": "Specific validated scale (e.g., PANAS, STAI-S)",
          "timing": "When to measure (baseline, post, follow-up)"
        }}
      ],
      "time_points": ["baseline", "post_manipulation", ...],
      "design_notes": ["Important consideration 1", "Important consideration 2"]
    }}

    Be specific about:
    1. How to operationalize each IV (manipulation or grouping)
    2. Which validated scales to use for each DV
    3. When to collect each measure
    4. Any design considerations (counterbalancing, randomization)
    """
    
    llm_manager = LLMManager()
    
    try:
        response = await llm_manager.chat(
            prompt=prompt,
            provider="openai",
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # Parse JSON response
        design_data = json.loads(response)
        logger.info("Successfully generated design proposal with LLM")
        return design_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Raw response: {response}")
        raise DesignProposalError(f"LLM response was not valid JSON: {e}")
    except Exception as e:
        logger.error(f"LLM design generation failed: {e}")
        raise DesignProposalError(f"Failed to generate design with LLM: {e}")


async def propose_design(
    project: ProjectState,
    constraints: Optional[DesignConstraints] = None,
    use_llm: bool = True
) -> DesignProposal:
    """Propose experimental design based on hypotheses.
    
    Args:
        project: Project state with hypotheses from Module 2
        constraints: Optional user constraints
        use_llm: If True, use LLM for enhanced proposal; if False, use heuristics only
        
    Returns:
        DesignProposal object
        
    Raises:
        DesignProposalError: If design proposal fails
    """
    logger.info("Starting design proposal")
    
    # Validate inputs
    if not project.hypotheses:
        raise DesignProposalError("No hypotheses found. Run Module 2 first.")
    
    hypotheses = project.hypotheses[:10]  # Limit to 10 for computational efficiency
    logger.info(f"Proposing design for {len(hypotheses)} hypotheses")
    
    # Step 1: Determine design type (heuristic)
    design_type = _determine_design_type(hypotheses)
    logger.info(f"Determined design type: {design_type}")
    
    # Step 2: Create conditions (heuristic baseline)
    conditions = _create_conditions(hypotheses)
    
    # Step 3: Map DVs to measures
    measures = _map_dvs_to_measures(hypotheses, project.concepts)
    
    # Step 4: Determine time points
    time_points = _determine_time_points(hypotheses)
    
    # Step 5: Generate rationale and refine with LLM (if available and enabled)
    rationale = f"Proposed {design_type} design based on hypothesis structure."
    design_notes = []
    
    if use_llm and LLM_AVAILABLE and config.is_provider_available("openai"):
        try:
            llm_design = await _generate_design_with_llm(
                hypotheses, design_type, constraints, project
            )
            
            # Enhance with LLM-generated details
            rationale = llm_design.get("rationale", rationale)
            design_notes = llm_design.get("design_notes", [])
            
            # Override conditions with LLM suggestions if provided
            if "conditions" in llm_design and llm_design["conditions"]:
                conditions = [
                    Condition(
                        id=f"cond_{i+1:02d}",
                        label=c["label"],
                        description=c.get("description", "") + " " + c.get("manipulation", "")
                    )
                    for i, c in enumerate(llm_design["conditions"])
                ]
            
            # Override measures with LLM suggestions if provided
            if "measures" in llm_design and llm_design["measures"]:
                measures = [
                    Measure(
                        id=f"measure_{i+1:02d}",
                        label=m["dv_name"],
                        scale=m["scale"],
                        time_points=[m["timing"]] if isinstance(m["timing"], str) else m["timing"]
                    )
                    for i, m in enumerate(llm_design["measures"])
                ]
            
            # Override time points if provided
            if "time_points" in llm_design:
                time_points = llm_design["time_points"]
            
            logger.info("Enhanced design proposal with LLM")
            
        except DesignProposalError as e:
            logger.warning(f"LLM enhancement failed, using heuristic baseline: {e}")
            # Continue with heuristic design
    
    # Create final proposal
    proposal = DesignProposal(
        design_type=design_type,
        conditions=conditions,
        measures=measures,
        time_points=time_points,
        rationale=rationale,
        design_notes=design_notes
    )
    
    logger.info(
        f"Design proposal complete: {len(conditions)} conditions, "
        f"{len(measures)} measures, {len(time_points)} time points"
    )
    
    return proposal
