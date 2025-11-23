"""Persona Modeling for Synthetic Participants.

Creates diverse persona templates representing different participant profiles.
Personas include attachment styles, personality traits, cultural backgrounds,
and other relevant characteristics.
"""

import logging
import random
from typing import List, Dict, Any
import uuid

from copilot_workflow.schemas import Persona, ExperimentDesign

logger = logging.getLogger(__name__)


class PersonaGenerator:
    """Generates diverse persona templates for simulation."""
    
    # Predefined persona characteristics
    ATTACHMENT_STYLES = [
        "secure",
        "anxious",
        "avoidant",
        "fearful-avoidant"
    ]
    
    SELF_CRITICISM_LEVELS = ["low", "medium", "high"]
    
    CULTURES = [
        "individualistic",
        "collectivistic",
        "mixed"
    ]
    
    # Big Five personality traits (0-100 scale)
    PERSONALITY_TRAITS = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism"
    ]
    
    def __init__(self):
        """Initialize the persona generator."""
        logger.info("PersonaGenerator initialized")
    
    def create_personas(self, n_participants: int, design: ExperimentDesign) -> List[Persona]:
        """Generate a diverse set of personas.
        
        Args:
            n_participants: Number of personas to generate
            design: Experimental design (for context)
            
        Returns:
            List of Persona objects
        """
        personas = []
        
        # Ensure balanced distribution across key characteristics
        # For attachment styles: distribute evenly
        n_per_style = n_participants // len(self.ATTACHMENT_STYLES)
        attachment_pool = []
        for style in self.ATTACHMENT_STYLES:
            attachment_pool.extend([style] * n_per_style)
        
        # Fill remaining slots randomly
        while len(attachment_pool) < n_participants:
            attachment_pool.append(random.choice(self.ATTACHMENT_STYLES))
        
        random.shuffle(attachment_pool)
        
        # Generate personas
        for i in range(n_participants):
            persona = self._generate_persona(
                attachment_style=attachment_pool[i],
                persona_id=f"persona_{i+1:04d}"
            )
            personas.append(persona)
        
        logger.info(f"Generated {len(personas)} diverse personas")
        return personas
    
    def _generate_persona(self, attachment_style: str, persona_id: str) -> Persona:
        """Generate a single persona with realistic characteristics.
        
        Args:
            attachment_style: Assigned attachment style
            persona_id: Unique identifier
            
        Returns:
            Persona object
        """
        # Generate personality traits
        personality_traits = {}
        for trait in self.PERSONALITY_TRAITS:
            # Base score: random between 30-70
            base_score = random.uniform(30, 70)
            
            # Adjust based on attachment style for coherence
            if attachment_style == "anxious":
                if trait == "neuroticism":
                    base_score += 15  # Higher neuroticism
                elif trait == "extraversion":
                    base_score -= 10  # Slightly lower extraversion
            elif attachment_style == "avoidant":
                if trait == "openness":
                    base_score -= 10
                elif trait == "agreeableness":
                    base_score -= 10
            elif attachment_style == "secure":
                if trait == "agreeableness":
                    base_score += 10
                elif trait == "neuroticism":
                    base_score -= 10
            
            # Clamp to 0-100 range
            personality_traits[trait] = max(0, min(100, base_score))
        
        # Select self-criticism level (correlated with neuroticism)
        if personality_traits["neuroticism"] > 60:
            self_criticism = random.choice(["medium", "high"])
        elif personality_traits["neuroticism"] < 40:
            self_criticism = random.choice(["low", "medium"])
        else:
            self_criticism = random.choice(self.SELF_CRITICISM_LEVELS)
        
        # Select culture
        culture = random.choice(self.CULTURES)
        
        # Generate demographic info
        age = random.randint(18, 65)
        gender = random.choice(["male", "female", "non-binary"])
        
        # Additional traits that might affect responses
        other_traits = {
            "age": age,
            "gender": gender,
            "education_level": random.choice(["high_school", "undergraduate", "graduate", "postgraduate"]),
            "relationship_status": random.choice(["single", "dating", "committed", "married"]),
            "stress_level": random.uniform(1, 7),  # 1-7 scale
            "social_support": random.uniform(1, 7),  # 1-7 scale
        }
        
        return Persona(
            attachment_style=attachment_style,
            self_criticism=self_criticism,
            culture=culture,
            personality_traits=personality_traits,
            demographic_info={"age": age, "gender": gender},
            other_traits=other_traits
        )


def create_personas(n_participants: int, design: ExperimentDesign) -> List[Persona]:
    """Convenience function to create personas.
    
    Args:
        n_participants: Number of personas to generate
        design: Experimental design
        
    Returns:
        List of Persona objects
    """
    generator = PersonaGenerator()
    return generator.create_personas(n_participants, design)
