"""Module 3: Experimental Design Builder & Critic.

Transforms hypotheses into concrete experimental designs with:
- Design type selection (between/within/mixed)
- Condition and measure specifications
- Confound validation
- Sample size recommendations
- APA Methods section generation
"""

from Experimental_Design_Builder_Critic.design_proposer import (
    propose_design,
    DesignConstraints,
    DesignProposal,
    DesignProposalError,
)
from Experimental_Design_Builder_Critic.confound_checker import (
    check_confounds,
    format_confound_report,
    ConfoundWarning,
)
from Experimental_Design_Builder_Critic.sample_size_calculator import (
    calculate_sample_size,
    get_effect_size_recommendations,
    format_sample_size_report,
    SampleSizePlan,
)
from Experimental_Design_Builder_Critic.methods_writer import (
    write_methods_section,
    format_methods_for_export,
    MethodsWriterError,
)
from Experimental_Design_Builder_Critic.run import run, run_with_summary, Module3Error

__all__ = [
    # Main functions
    "run",
    "run_with_summary",
    # Design proposer
    "propose_design",
    "DesignConstraints",
    "DesignProposal",
    "DesignProposalError",
    # Confound checker
    "check_confounds",
    "format_confound_report",
    "ConfoundWarning",
    # Sample size calculator
    "calculate_sample_size",
    "get_effect_size_recommendations",
    "format_sample_size_report",
    "SampleSizePlan",
    # Methods writer
    "write_methods_section",
    "format_methods_for_export",
    "MethodsWriterError",
    # Errors
    "Module3Error",
]
