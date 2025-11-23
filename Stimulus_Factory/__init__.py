"""Module 4: Stimulus Factory

Generates balanced, annotated experimental stimuli with:
- Scenario/vignette generation with systematic variation
- Automatic metadata annotation (valence, intensity, themes)
- Balance optimization across conditions
- Content filtering for safety

Main Functions:
- run(project) -> ProjectState: Main orchestration function
- run_with_summary(project) -> (ProjectState, summary): Run with metrics
- generate_stimuli(design) -> List[StimulusItem]: Generate stimuli
- annotate_stimuli(stimuli) -> List[StimulusItem]: Add metadata
- balance_stimuli_across_conditions(stimuli) -> List[StimulusItem]: Balance
- filter_stimuli(stimuli) -> (kept, flagged): Content filtering
"""

from .run import run, run_with_summary, Module4Error
from .stimulus_generator import (
    generate_stimuli,
    StimulusGenerationError,
)
from .metadata_annotator import (
    annotate_stimuli,
    get_metadata_summary,
    MetadataAnnotationError,
)
from .balance_optimizer import (
    balance_stimuli_across_conditions,
    calculate_balance_score,
    BalanceOptimizationError,
)
from .content_filter import (
    filter_stimuli,
    get_filter_summary,
    ContentFilterError,
)

__all__ = [
    # Main functions
    "run",
    "run_with_summary",
    "Module4Error",
    # Stimulus generation
    "generate_stimuli",
    "StimulusGenerationError",
    # Metadata annotation
    "annotate_stimuli",
    "get_metadata_summary",
    "MetadataAnnotationError",
    # Balance optimization
    "balance_stimuli_across_conditions",
    "calculate_balance_score",
    "BalanceOptimizationError",
    # Content filtering
    "filter_stimuli",
    "get_filter_summary",
    "ContentFilterError",
]
