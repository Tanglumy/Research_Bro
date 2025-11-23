"""Metadata Annotator: Automatically labels stimuli with metadata.

Annotates each stimulus with:
- Valence (positive, negative, neutral, mixed)
- Intensity (low, medium, high)
- Relationship type (romantic, friend, family, work, other)
- Emotional themes (anxiety, conflict, support, etc.)
- Ambiguity level (low, medium, high)
- Length metrics (word count, reading time)
"""

import json
import logging
from typing import List, Dict

from copilot_workflow.config import get_config
from copilot_workflow.schemas import (
    StimulusItem,
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


class MetadataAnnotationError(Exception):
    """Raised when metadata annotation fails."""
    pass


# Keyword-based heuristics
VALENCE_KEYWORDS = {
    "positive": ["happy", "joy", "excited", "love", "success", "proud", "grateful"],
    "negative": ["sad", "angry", "upset", "hurt", "disappointed", "frustrated", "anxious"],
}

INTENSITY_KEYWORDS = {
    "high": ["extremely", "very", "incredibly", "devastated", "furious"],
    "low": ["slightly", "somewhat", "a little", "mildly"],
}

RELATIONSHIP_KEYWORDS = {
    "romantic": ["partner", "boyfriend", "girlfriend", "spouse"],
    "friend": ["friend", "buddy", "pal"],
    "family": ["parent", "mother", "father", "sibling"],
    "work": ["coworker", "colleague", "boss", "manager"],
}

EMOTIONAL_THEMES = {
    "anxiety": ["anxious", "worried", "nervous"],
    "conflict": ["argument", "fight", "disagree"],
    "support": ["support", "help", "comfort"],
}


def _annotate_with_heuristics(stimulus: StimulusItem) -> StimulusMetadata:
    text = stimulus.text.lower()
    assigned_condition = stimulus.metadata.assigned_condition if stimulus.metadata else None
    
    # Valence
    pos = sum(1 for w in VALENCE_KEYWORDS["positive"] if w in text)
    neg = sum(1 for w in VALENCE_KEYWORDS["negative"] if w in text)
    valence = "mixed" if pos > 0 and neg > 0 else ("positive" if pos > neg else ("negative" if neg > 0 else "neutral"))
    
    # Intensity
    high = sum(1 for w in INTENSITY_KEYWORDS["high"] if w in text)
    low = sum(1 for w in INTENSITY_KEYWORDS["low"] if w in text)
    intensity = "high" if high > 0 else ("low" if low > 0 else "medium")
    
    # Relationship
    rel_scores = {k: sum(1 for w in v if w in text) for k, v in RELATIONSHIP_KEYWORDS.items()}
    relationship_type = max(rel_scores, key=rel_scores.get) if max(rel_scores.values()) > 0 else "other"
    
    # Themes
    themes = [theme for theme, words in EMOTIONAL_THEMES.items() if any(w in text for w in words)]
    
    # Length
    words = stimulus.text.split()
    word_count = len(words)
    reading_time = max(3, int((word_count / 250) * 60))
    
    return StimulusMetadata(
        valence=valence,
        intensity=intensity,
        relationship_type=relationship_type,
        emotional_themes=themes,
        ambiguity_level="medium",
        word_count=word_count,
        reading_time_seconds=reading_time,
        assigned_condition=assigned_condition
    )


async def annotate_stimuli(
    stimuli: List[StimulusItem],
    use_llm: bool = True
) -> List[StimulusItem]:
    logger.info(f"Annotating {len(stimuli)} stimuli")
    
    for stimulus in stimuli:
        stimulus.metadata = _annotate_with_heuristics(stimulus)
    
    logger.info(f"Annotated {len(stimuli)} stimuli with heuristics")
    return stimuli


def get_metadata_summary(stimuli: List[StimulusItem]) -> Dict:
    if not stimuli:
        return {}
    
    valence = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    intensity = {"low": 0, "medium": 0, "high": 0}
    relationship = {"romantic": 0, "friend": 0, "family": 0, "work": 0, "other": 0}
    
    for s in stimuli:
        if s.metadata:
            valence[s.metadata.valence] = valence.get(s.metadata.valence, 0) + 1
            intensity[s.metadata.intensity] = intensity.get(s.metadata.intensity, 0) + 1
            relationship[s.metadata.relationship_type] = relationship.get(s.metadata.relationship_type, 0) + 1
    
    return {
        "valence_distribution": valence,
        "intensity_distribution": intensity,
        "relationship_distribution": relationship
    }
