"""Stimulus Generator: Core Module 4 component for generating experimental stimuli.

Generates diverse scenarios, vignettes, and dialogues with systematic variation
across experimental conditions using LLM-powered generation with template fallback.
"""

import json
import logging
import random
from typing import List, Optional, Dict
from dataclasses import asdict

from copilot_workflow.config import get_config
from copilot_workflow.schemas import (
    ProjectState,
    ExperimentDesign,
    Condition,
    StimulusItem,
    StimulusVariant,
    StimulusMetadata,
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


class StimulusGenerationError(Exception):
    """Raised when stimulus generation fails."""
    pass


# Template-based fallback scenarios (for when LLM unavailable)
TEMPLATE_SCENARIOS = {
    "romantic": [
        "Your partner hasn't replied to your texts for several hours.",
        "You're planning a surprise date night for your partner.",
        "Your partner seems distant and distracted lately.",
        "You and your partner are discussing moving in together.",
        "Your partner forgot an important anniversary.",
    ],
    "friend": [
        "Your best friend forgot to invite you to their birthday party.",
        "A friend asks you for help with a big project.",
        "You notice your friend has been avoiding you recently.",
        "Your friend is going through a difficult breakup.",
        "A friend cancels plans with you at the last minute.",
    ],
    "work": [
        "Your boss gives critical feedback on your recent project.",
        "A coworker takes credit for your idea in a meeting.",
        "You're asked to present to senior leadership tomorrow.",
        "A colleague asks you to cover for them during an important deadline.",
        "Your team is reorganizing and your role may change.",
    ],
    "family": [
        "Your parent disagrees with an important life decision you made.",
        "A family member asks to borrow money from you.",
        "You're hosting a holiday gathering and feeling overwhelmed.",
        "A sibling shares news that makes you feel left out.",
        "Your family is planning a reunion but you have other commitments.",
    ],
}


def _create_generation_prompt(
    condition: Condition,
    style: str,
    num_stimuli: int,
    relationship_types: Optional[List[str]] = None
) -> str:
    """Create LLM prompt for stimulus generation.
    
    Args:
        condition: Experimental condition to generate for
        style: Generation style (scenario, dialogue, vignette)
        num_stimuli: Number of stimuli to generate
        relationship_types: Types of relationships to include
        
    Returns:
        Formatted prompt string
    """
    relationship_types = relationship_types or ["romantic", "friend", "family", "work"]
    
    style_instructions = {
        "scenario": "brief scenarios (2-3 sentences) describing realistic situations",
        "dialogue": "short dialogues (4-6 exchanges) between characters",
        "vignette": "detailed vignettes (4-5 sentences) with rich context and emotional depth"
    }
    
    prompt = f"""You are generating experimental stimuli for a psychology study.

Condition: {condition.label}
Manipulation: {condition.manipulation_description or 'Participants in this condition...'}

Task: Generate {num_stimuli} diverse, realistic {style_instructions.get(style, style)} that reflect this condition.

Requirements:
1. Relationship types: Include mix of {', '.join(relationship_types)}
2. Emotional range: Mix of positive, negative, and neutral valence
3. Intensity levels: Include low, medium, and high intensity situations
4. Realism: Situations should be plausible and relatable
5. Diversity: Avoid repetition; each stimulus should be unique
6. Clarity: Clear enough for participants to understand and respond to

Style Guidelines for {style}:
- Keep language natural and conversational
- Avoid overly dramatic or extreme scenarios
- Use "you" perspective (second person)
- Be culturally sensitive and appropriate
- Length: {style_instructions.get(style, '2-3 sentences')}

Output Format:
{{
  "stimuli": [
    {{
      "text": "Stimulus text here...",
      "relationship_type": "romantic|friend|family|work|other",
      "brief_description": "One sentence summary"
    }}
  ]
}}

Generate {num_stimuli} diverse stimuli now.
"""
    
    return prompt


def _extract_stimuli_from_response(response: str) -> List[Dict]:
    """Extract stimulus data from LLM JSON response.
    
    Args:
        response: LLM response string (should be JSON)
        
    Returns:
        List of stimulus dicts with text and metadata
        
    Raises:
        StimulusGenerationError: If response parsing fails
    """
    try:
        # Parse JSON response
        data = json.loads(response)
        
        # Extract stimuli array
        if "stimuli" in data:
            return data["stimuli"]
        elif isinstance(data, list):
            return data
        else:
            raise StimulusGenerationError("Response missing 'stimuli' array")
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Raw response: {response}")
        raise StimulusGenerationError(f"Invalid JSON response: {e}")
    except Exception as e:
        logger.error(f"Failed to extract stimuli: {e}")
        raise StimulusGenerationError(f"Stimulus extraction failed: {e}")


def _create_stimulus_variants(
    base_text: str,
    condition: Condition,
    variant_type: str = "original"
) -> List[StimulusVariant]:
    """Create stimulus variants for different conditions.
    
    Args:
        base_text: Base stimulus text
        condition: Condition this variant is for
        variant_type: Type of variant
        
    Returns:
        List of StimulusVariant objects
    """
    # For now, just create original variant
    # Future: Could create manipulation-specific variants
    variants = [
        StimulusVariant(
            id=f"{condition.id}_v1",
            variant_type=variant_type,
            text=base_text
        )
    ]
    
    return variants


def _generate_template_stimuli(
    condition: Condition,
    num_stimuli: int,
    relationship_types: Optional[List[str]] = None
) -> List[StimulusItem]:
    """Generate stimuli using templates (fallback when LLM unavailable).
    
    Args:
        condition: Experimental condition
        num_stimuli: Number of stimuli to generate
        relationship_types: Types of relationships to include
        
    Returns:
        List of StimulusItem objects
    """
    relationship_types = relationship_types or list(TEMPLATE_SCENARIOS.keys())
    
    stimuli = []
    stim_id = 1
    
    # Cycle through relationship types and templates
    while len(stimuli) < num_stimuli:
        for rel_type in relationship_types:
            if len(stimuli) >= num_stimuli:
                break
            
            # Get templates for this relationship type
            templates = TEMPLATE_SCENARIOS.get(rel_type, [])
            if not templates:
                continue
            
            # Pick a random template
            template = random.choice(templates)
            
            # Create stimulus item
            stimulus = StimulusItem(
                id=f"stim_{stim_id:03d}",
                text=template,
                language="en",
                metadata=StimulusMetadata(assigned_condition=condition.id),
                variants=_create_stimulus_variants(template, condition)
            )
            
            stimuli.append(stimulus)
            stim_id += 1
    
    logger.info(f"Generated {len(stimuli)} template-based stimuli for condition {condition.label}")
    return stimuli[:num_stimuli]


async def _generate_with_llm(
    condition: Condition,
    num_stimuli: int,
    style: str,
    relationship_types: Optional[List[str]],
    retries: int = 3
) -> List[StimulusItem]:
    """Generate stimuli using LLM.
    
    Args:
        condition: Experimental condition
        num_stimuli: Number of stimuli to generate
        style: Generation style
        relationship_types: Types of relationships
        retries: Number of retry attempts
        
    Returns:
        List of StimulusItem objects
        
    Raises:
        StimulusGenerationError: If generation fails after retries
    """
    if not LLM_AVAILABLE:
        raise StimulusGenerationError("LLM not available for stimulus generation")
    
    if not config.is_provider_available("openai"):
        raise StimulusGenerationError("OpenAI not available. Check OPENAI_API_KEY in .env")
    
    # Create generation prompt
    prompt = _create_generation_prompt(condition, style, num_stimuli, relationship_types)
    
    llm_manager = LLMManager()
    
    # Retry loop
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Generating {num_stimuli} stimuli with LLM (attempt {attempt}/{retries})")
            
            response = await llm_manager.chat(
                prompt=prompt,
                provider="openai",
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            
            # Extract stimuli from response
            stimuli_data = _extract_stimuli_from_response(response)
            
            # Convert to StimulusItem objects
            stimuli = []
            for i, stim_dict in enumerate(stimuli_data[:num_stimuli], 1):
                stimulus = StimulusItem(
                    id=f"stim_{i:03d}",
                    text=stim_dict.get("text", ""),
                    language="en",
                    metadata=StimulusMetadata(assigned_condition=condition.id),
                    variants=_create_stimulus_variants(
                        stim_dict.get("text", ""),
                        condition
                    )
                )
                stimuli.append(stimulus)
            
            logger.info(f"Successfully generated {len(stimuli)} stimuli with LLM")
            return stimuli
            
        except (StimulusGenerationError, json.JSONDecodeError) as e:
            logger.warning(f"LLM generation attempt {attempt} failed: {e}")
            if attempt == retries:
                raise StimulusGenerationError(f"Failed to generate stimuli after {retries} attempts: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            raise StimulusGenerationError(f"LLM generation failed: {e}")
    
    raise StimulusGenerationError("Failed to generate stimuli with LLM")


async def generate_stimuli(
    design: ExperimentDesign,
    num_stimuli_per_condition: int = 10,
    style: str = "scenario",
    relationship_types: Optional[List[str]] = None,
    use_llm: bool = True
) -> List[StimulusItem]:
    """Generate experimental stimuli for all conditions.
    
    Args:
        design: Experimental design from Module 3
        num_stimuli_per_condition: Number of stimuli to generate per condition
        style: Generation style (scenario, dialogue, vignette)
        relationship_types: Types of relationships to include
        use_llm: Whether to use LLM (if False, use templates)
        
    Returns:
        List of StimulusItem objects across all conditions
        
    Raises:
        StimulusGenerationError: If generation fails
    """
    logger.info("Starting stimulus generation")
    logger.info(
        f"  Conditions: {len(design.conditions)}"
    )
    logger.info(f"  Stimuli per condition: {num_stimuli_per_condition}")
    logger.info(f"  Style: {style}")
    logger.info(f"  Use LLM: {use_llm}")
    
    # Validate inputs
    if not design.conditions:
        raise StimulusGenerationError("No conditions in design. Run Module 3 first.")
    
    if num_stimuli_per_condition < 1:
        raise StimulusGenerationError("num_stimuli_per_condition must be at least 1")
    
    if style not in ["scenario", "dialogue", "vignette"]:
        logger.warning(f"Unknown style '{style}', using 'scenario'")
        style = "scenario"
    
    all_stimuli = []
    
    # Generate stimuli for each condition
    for condition in design.conditions:
        logger.info(f"\nGenerating stimuli for condition: {condition.label}")
        
        try:
            # Try LLM-based generation first
            if use_llm and LLM_AVAILABLE and config.is_provider_available("openai"):
                try:
                    stimuli = await _generate_with_llm(
                        condition,
                        num_stimuli_per_condition,
                        style,
                        relationship_types
                    )
                    all_stimuli.extend(stimuli)
                    logger.info(f"  ✓ Generated {len(stimuli)} stimuli with LLM")
                    continue
                    
                except StimulusGenerationError as e:
                    logger.warning(f"  LLM generation failed: {e}")
                    logger.info("  Falling back to template-based generation")
            
            # Fallback to template-based generation
            stimuli = _generate_template_stimuli(
                condition,
                num_stimuli_per_condition,
                relationship_types
            )
            all_stimuli.extend(stimuli)
            logger.info(f"  ✓ Generated {len(stimuli)} stimuli with templates")
            
        except Exception as e:
            logger.error(f"  ✗ Failed to generate stimuli for {condition.label}: {e}")
            # Continue with other conditions instead of failing completely
            continue
    
    if not all_stimuli:
        raise StimulusGenerationError(
            "Failed to generate any stimuli. Check conditions and LLM availability."
        )
    
    logger.info(f"\nStimulus generation complete:")
    logger.info(f"  Total stimuli: {len(all_stimuli)}")
    covered_conditions = {
        s.metadata.assigned_condition
        for s in all_stimuli
        if getattr(s, "metadata", None) and s.metadata.assigned_condition
    }
    logger.info(f"  Conditions covered: {len(covered_conditions)}")
    
    return all_stimuli
