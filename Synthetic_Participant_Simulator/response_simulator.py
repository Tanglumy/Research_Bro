"""Response Simulator for Synthetic Participants.

Simulates participant responses based on persona characteristics,
stimulus properties, and experimental design.
Generates both quantitative DV scores and qualitative text responses.
"""

import logging
import random
import uuid
from typing import Dict, Any, List

from copilot_workflow.schemas import (
    Persona,
    StimulusItem,
    ExperimentDesign,
    SyntheticResponse,
    Measure
)

logger = logging.getLogger(__name__)


class ResponseSimulator:
    """Simulates participant responses to stimuli."""
    
    def __init__(self):
        """Initialize the response simulator."""
        logger.info("ResponseSimulator initialized")
    
    async def simulate_response(
        self,
        persona: Persona,
        stimulus: StimulusItem,
        design: ExperimentDesign
    ) -> SyntheticResponse:
        """Simulate a participant's response to a stimulus.
        
        Args:
            persona: Participant persona
            stimulus: Stimulus item
            design: Experimental design
            
        Returns:
            SyntheticResponse with DV scores and open text
        """
        # Generate DV scores for all measures
        dv_scores = {}
        
        for measure in design.measures:
            score = self._generate_dv_score(
                persona=persona,
                stimulus=stimulus,
                measure=measure
            )
            dv_scores[measure.label] = score
        
        # Generate open-text response if applicable
        open_text = self._generate_open_text(
            persona=persona,
            stimulus=stimulus
        )
        
        return SyntheticResponse(
            stimulus_id=stimulus.id,
            condition_id=stimulus.metadata.assigned_condition or "unknown",
            dv_scores=dv_scores,
            open_text=open_text
        )
    
    def _generate_dv_score(
        self,
        persona: Persona,
        stimulus: StimulusItem,
        measure: Measure
    ) -> float:
        """Generate a DV score based on persona and stimulus characteristics.
        
        Args:
            persona: Participant persona
            stimulus: Stimulus item
            measure: Measure to score
            
        Returns:
            Simulated score (typically on 1-7 Likert scale)
        """
        # Base score: random with person-specific bias
        # Use neuroticism as a general negative affect bias
        neuroticism = persona.personality_traits.get("neuroticism", 50) / 100
        
        # Start with a base score around the midpoint
        base_score = 4.0  # Midpoint of 1-7 scale
        
        # Adjust based on stimulus valence
        if stimulus.metadata.valence == "negative":
            # Negative stimuli increase negative affect
            base_score += neuroticism * 2.0
            
            # Anxious attachment -> higher reactivity
            if persona.attachment_style == "anxious":
                base_score += 0.8
        elif stimulus.metadata.valence == "positive":
            # Positive stimuli decrease negative affect
            base_score -= 0.5
            
            # Secure attachment -> more positive response
            if persona.attachment_style == "secure":
                base_score -= 0.5
        
        # Adjust based on stimulus intensity
        intensity_factor = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5
        }.get(stimulus.metadata.intensity, 1.0)
        
        base_score = 4.0 + (base_score - 4.0) * intensity_factor
        
        # Adjust based on self-criticism for relevant measures
        if "anxiety" in measure.label.lower() or "stress" in measure.label.lower():
            if persona.self_criticism == "high":
                base_score += 0.7
            elif persona.self_criticism == "low":
                base_score -= 0.5
        
        # Add individual variability (random noise)
        noise = random.gauss(0, 0.5)  # Small random variation
        base_score += noise
        
        # Clamp to scale range (1-7)
        return max(1.0, min(7.0, base_score))
    
    def _generate_open_text(
        self,
        persona: Persona,
        stimulus: StimulusItem
    ) -> str:
        """Generate qualitative open-text response.
        
        Args:
            persona: Participant persona
            stimulus: Stimulus item
            
        Returns:
            Simulated text response
        """
        # Template-based generation based on persona characteristics
        
        # Determine response style based on personality
        extraversion = persona.personality_traits.get("extraversion", 50)
        openness = persona.personality_traits.get("openness", 50)
        neuroticism = persona.personality_traits.get("neuroticism", 50)
        
        # Response templates by attachment style
        templates = {
            "anxious": [
                "This situation really worries me. I feel {emotion} and can't stop thinking about what might go wrong.",
                "I'm feeling quite {emotion} about this. I keep replaying the scenario in my mind.",
                "This makes me feel {emotion}. I would probably seek reassurance from others."
            ],
            "avoidant": [
                "I don't think this would affect me much. I prefer to handle things independently.",
                "This situation is {emotion}, but I would likely distance myself emotionally.",
                "I would try not to dwell on this. It's better to stay self-reliant."
            ],
            "secure": [
                "This situation feels {emotion}, but I think I could manage it with support if needed.",
                "I feel {emotion} about this, and I would communicate my feelings openly.",
                "This makes me feel {emotion}, but I'm confident I can cope with it."
            ],
            "fearful-avoidant": [
                "This situation is confusing. Part of me wants to {action}, but another part wants to withdraw.",
                "I feel {emotion} and uncertain about how to respond. I might alternate between seeking help and avoiding it.",
                "This creates mixed feelings. I'm both {emotion} and hesitant to engage fully."
            ]
        }
        
        # Select template
        style = persona.attachment_style or "secure"
        template = random.choice(templates.get(style, templates["secure"]))
        
        # Fill in emotion based on stimulus valence
        emotions = {
            "negative": ["anxious", "stressed", "uncomfortable", "worried", "upset"],
            "positive": ["happy", "content", "relieved", "pleased", "calm"],
            "neutral": ["neutral", "uncertain", "okay", "mixed"],
            "mixed": ["conflicted", "ambivalent", "uncertain", "torn"]
        }
        
        emotion = random.choice(emotions.get(stimulus.metadata.valence, emotions["neutral"]))
        action = random.choice(["reach out", "connect", "engage", "respond"])
        
        # Adjust response length based on openness
        response = template.format(emotion=emotion, action=action)
        
        # More open individuals tend to elaborate
        if openness > 60 and random.random() > 0.5:
            elaborations = [
                " I think this relates to past experiences.",
                " This reminds me of similar situations.",
                " I would want to understand the deeper meaning."
            ]
            response += random.choice(elaborations)
        
        return response


# Example usage helper
def simulate_responses(
    personas: List[Persona],
    stimuli: List[StimulusItem],
    design: ExperimentDesign
) -> Dict[str, List[SyntheticResponse]]:
    """Simulate responses for multiple personas and stimuli.
    
    Args:
        personas: List of personas
        stimuli: List of stimuli
        design: Experimental design
        
    Returns:
        Dictionary mapping persona IDs to their responses
    """
    simulator = ResponseSimulator()
    results = {}
    
    import asyncio
    
    async def simulate_all():
        for i, persona in enumerate(personas):
            persona_responses = []
            for stimulus in stimuli:
                response = await simulator.simulate_response(persona, stimulus, design)
                persona_responses.append(response)
            results[f"persona_{i}"] = persona_responses
    
    asyncio.run(simulate_all())
    return results
