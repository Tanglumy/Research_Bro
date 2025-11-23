"""Module 2: Hypothesis Generator & Structurer

Generates structured, testable hypotheses from literature knowledge graph.

Main Functions:
- run(project) -> ProjectState: Main orchestration function
- run_with_summary(project) -> (ProjectState, summary): Run with metrics
- generate_hypotheses(project) -> HypothesisGenerationResult: Generate hypotheses
- validate_hypotheses(hypotheses) -> List[ValidationResult]: Validate quality
- export_to_json(hypotheses) -> str: Export as JSON
- export_to_markdown_table(hypotheses) -> str: Export as markdown
"""

from .run import run, run_with_summary, Module2Error
from .hypothesis_generator import (
    generate_hypotheses,
    HypothesisGenerationError,
    HypothesisGenerationResult
)
from .hypothesis_validator import (
    validate_hypothesis,
    validate_hypotheses,
    HypothesisValidationResult
)
from .hypothesis_exporter import (
    export_to_json,
    export_to_markdown_table,
    export_with_validation,
    export_summary_stats,
    generate_hypothesis_report
)

__all__ = [
    # Main functions
    "run",
    "run_with_summary",
    "Module2Error",
    # Generation
    "generate_hypotheses",
    "HypothesisGenerationError",
    "HypothesisGenerationResult",
    # Validation
    "validate_hypothesis",
    "validate_hypotheses",
    "HypothesisValidationResult",
    # Export
    "export_to_json",
    "export_to_markdown_table",
    "export_with_validation",
    "export_summary_stats",
    "generate_hypothesis_report",
]
