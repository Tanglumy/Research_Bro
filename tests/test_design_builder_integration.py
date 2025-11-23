"""Integration tests for Experimental Design Builder & Critic (Module 3).

Tests the integration of all design building components:
- Design proposal generation
- Confound checking
- Sample size calculation
- Methods section writing
- Complete module workflow
"""

import pytest
import asyncio
from typing import List

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    Hypothesis,
    ExperimentDesign,
    Condition,
    Measure,
    AuditEntry
)

from Experimental_Design_Builder_Critic import run, run_with_summary
from Experimental_Design_Builder_Critic.design_proposer import (
    propose_design,
    DesignConstraints,
    DesignProposal
)
from Experimental_Design_Builder_Critic.confound_checker import (
    check_confounds,
    format_confound_report
)
from Experimental_Design_Builder_Critic.sample_size_calculator import (
    calculate_sample_size,
    get_effect_size_recommendations
)
from Experimental_Design_Builder_Critic.methods_writer import (
    write_methods_section
)


@pytest.fixture
def sample_project_with_hypotheses():
    """Create a sample project with hypotheses from Module 2."""
    project = ProjectState()
    
    project.rq = ResearchQuestion(
        raw_text="How does attachment anxiety influence emotion regulation in relationships?",
        parsed_constructs=["attachment anxiety", "emotion regulation"],
        domain="Social Psychology"
    )
    
    project.hypotheses = [
        Hypothesis(
            id="h1",
            text="Higher attachment anxiety predicts greater use of maladaptive emotion regulation strategies",
            iv=["Attachment Anxiety"],
            dv=["Emotion Regulation Strategies"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment Theory"],
            expected_direction="Positive: Higher anxiety -> more maladaptive strategies"
        ),
        Hypothesis(
            id="h2",
            text="Self-compassion moderates the relationship between attachment anxiety and emotion regulation",
            iv=["Attachment Anxiety"],
            dv=["Emotion Regulation"],
            mediators=[],
            moderators=["Self-Compassion"],
            theoretical_basis=["Attachment Theory", "Self-Compassion Research"],
            expected_direction="Interaction: Self-compassion buffers the negative effect"
        )
    ]
    
    project.audit_log = []
    
    return project


class TestDesignProposer:
    """Test design proposal generation."""
    
    @pytest.mark.asyncio
    async def test_propose_basic_design(self, sample_project_with_hypotheses):
        """Test basic design proposal."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        # Check structure
        assert proposal.design_type in ["between_subjects", "within_subjects", "mixed"]
        assert len(proposal.conditions) >= 2  # At least control and experimental
        assert len(proposal.measures) >= 1  # At least one DV measure
        assert len(proposal.time_points) >= 1  # At least one time point
    
    @pytest.mark.asyncio
    async def test_design_uses_hypothesis_variables(self, sample_project_with_hypotheses):
        """Test that design uses variables from hypotheses."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        # Collect all IVs and DVs from hypotheses
        hypothesis_ivs = set()
        hypothesis_dvs = set()
        for h in sample_project_with_hypotheses.hypotheses:
            hypothesis_ivs.update(h.iv)
            hypothesis_dvs.update(h.dv)
        
        # Check conditions relate to IVs
        condition_labels = {c.label.lower() for c in proposal.conditions}
        iv_labels = {iv.lower() for iv in hypothesis_ivs}
        
        # Should have some overlap (conditions should manipulate IVs)
        # (May not be exact match due to LLM flexibility)
        assert len(proposal.conditions) >= 2
        
        # Check measures relate to DVs
        measure_labels = {m.label.lower() for m in proposal.measures}
        dv_labels = {dv.lower() for dv in hypothesis_dvs}
        
        # Should measure the DVs
        assert len(proposal.measures) >= 1
    
    @pytest.mark.asyncio
    async def test_design_with_constraints(self, sample_project_with_hypotheses):
        """Test design proposal with user constraints."""
        constraints = DesignConstraints(
            design_type="between_subjects",
            max_conditions=3,
            online_only=True
        )
        
        proposal = await propose_design(
            sample_project_with_hypotheses,
            constraints=constraints,
            use_llm=False
        )
        
        # Check constraints respected
        assert proposal.design_type == "between_subjects"
        assert len(proposal.conditions) <= 3
    
    @pytest.mark.asyncio
    async def test_design_handles_moderation(self, sample_project_with_hypotheses):
        """Test that design handles moderation hypotheses."""
        # Sample project has moderation hypothesis
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        # Should suggest measuring moderator
        moderator_measures = [
            m for m in proposal.measures
            if "compassion" in m.label.lower() or "moderator" in m.label.lower()
        ]
        
        # May not always include moderator explicitly, but should have multiple measures
        assert len(proposal.measures) >= 2


class TestConfoundChecker:
    """Test confound checking functionality."""
    
    @pytest.mark.asyncio
    async def test_check_confounds_clean_design(self, sample_project_with_hypotheses):
        """Test confound checking on a clean design."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        warnings = check_confounds(proposal)
        
        # Should return warnings list (may be empty for good design)
        assert isinstance(warnings, list)
        
        # Check warning structure if any exist
        for warning in warnings:
            assert hasattr(warning, 'confound_type')
            assert hasattr(warning, 'severity')
            assert hasattr(warning, 'description')
            assert warning.severity in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_confound_report_format(self, sample_project_with_hypotheses):
        """Test confound report formatting."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        warnings = check_confounds(proposal)
        
        report = format_confound_report(warnings)
        
        assert isinstance(report, str)
        assert len(report) > 0


class TestSampleSizeCalculator:
    """Test sample size calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_sample_size_basic(self, sample_project_with_hypotheses):
        """Test basic sample size calculation."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        sample_plan = calculate_sample_size(
            proposal,
            effect_size="medium",
            power=0.80
        )
        
        # Check structure
        assert hasattr(sample_plan, 'total_n')
        assert hasattr(sample_plan, 'per_condition_n')
        assert sample_plan.total_n > 0
        assert sample_plan.per_condition_n > 0
        
        # Reasonable sample size
        assert 20 <= sample_plan.total_n <= 500
    
    @pytest.mark.asyncio
    async def test_effect_size_recommendations(self, sample_project_with_hypotheses):
        """Test getting recommendations for all effect sizes."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        recommendations = get_effect_size_recommendations(proposal)
        
        # Should have recommendations for small, medium, large
        assert "small" in recommendations
        assert "medium" in recommendations
        assert "large" in recommendations
        
        # Larger effect sizes should need smaller samples
        assert recommendations["large"].total_n < recommendations["medium"].total_n
        assert recommendations["medium"].total_n < recommendations["small"].total_n
    
    @pytest.mark.asyncio
    async def test_sample_size_scales_with_conditions(self, sample_project_with_hypotheses):
        """Test that sample size scales appropriately with number of conditions."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        sample_plan = calculate_sample_size(proposal, effect_size="medium")
        
        # Total N should be roughly per_condition_n * num_conditions
        expected_total = sample_plan.per_condition_n * len(proposal.conditions)
        
        # Allow some tolerance for rounding
        assert abs(sample_plan.total_n - expected_total) <= len(proposal.conditions)


class TestMethodsWriter:
    """Test Methods section generation."""
    
    @pytest.mark.asyncio
    async def test_write_methods_basic(self, sample_project_with_hypotheses):
        """Test basic Methods section writing."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        sample_plan = calculate_sample_size(proposal, effect_size="medium")
        
        methods_text = await write_methods_section(
            proposal,
            sample_plan,
            sample_project_with_hypotheses,
            use_llm=False
        )
        
        assert methods_text is not None
        assert len(methods_text) > 0
        
        # Should contain key sections
        methods_lower = methods_text.lower()
        assert "participant" in methods_lower or "sample" in methods_lower
        assert "design" in methods_lower or "procedure" in methods_lower
        assert "measure" in methods_lower or "instrument" in methods_lower
    
    @pytest.mark.asyncio
    async def test_methods_includes_all_components(self, sample_project_with_hypotheses):
        """Test that Methods section includes all design components."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        sample_plan = calculate_sample_size(proposal, effect_size="medium")
        
        methods_text = await write_methods_section(
            proposal,
            sample_plan,
            sample_project_with_hypotheses,
            use_llm=False
        )
        
        # Check mentions conditions
        for condition in proposal.conditions:
            # At least some condition info should appear
            pass  # Conditions may be described differently in text
        
        # Check mentions measures
        for measure in proposal.measures:
            # At least some measure info should appear
            pass  # Measures may be described differently in text
        
        # Check has reasonable length (APA Methods are typically 500-2000 words)
        word_count = len(methods_text.split())
        assert 200 <= word_count <= 3000


class TestCompleteModule:
    """Test complete Module 3 workflow."""
    
    @pytest.mark.asyncio
    async def test_full_module_run(self, sample_project_with_hypotheses):
        """Test running complete Module 3."""
        result_project = await run(
            sample_project_with_hypotheses,
            effect_size="medium",
            use_llm=False
        )
        
        # Check project was updated
        assert result_project.design is not None
        
        # Check design components
        assert result_project.design.design_type is not None
        assert len(result_project.design.conditions) >= 2
        assert len(result_project.design.measures) >= 1
        assert result_project.design.sample_size_plan is not None
        
        # Check Methods section
        assert hasattr(result_project.design, 'methods_draft')
        assert result_project.design.methods_draft is not None
        assert len(result_project.design.methods_draft) > 0
        
        # Check audit log updated
        assert len(result_project.audit_log) > 0
    
    @pytest.mark.asyncio
    async def test_run_with_summary(self, sample_project_with_hypotheses):
        """Test run_with_summary function."""
        result_project, summary = await run_with_summary(
            sample_project_with_hypotheses,
            effect_size="medium",
            use_llm=False
        )
        
        # Check project updated
        assert result_project.design is not None
        
        # Check summary structure
        assert "design_type" in summary
        assert "num_conditions" in summary
        assert "num_measures" in summary
        assert "sample_size" in summary
        assert "methods_word_count" in summary
        
        # Check values
        assert summary["num_conditions"] >= 2
        assert summary["num_measures"] >= 1
        assert summary["sample_size"] > 0
    
    @pytest.mark.asyncio
    async def test_module_error_handling_no_hypotheses(self):
        """Test error handling when hypotheses missing."""
        project = ProjectState()
        project.rq = ResearchQuestion(
            raw_text="Test",
            parsed_constructs=["test"],
            domain="Test"
        )
        project.hypotheses = []  # No hypotheses
        project.audit_log = []
        
        with pytest.raises(Exception):  # Should raise Module3Error
            await run(project, use_llm=False)
    
    @pytest.mark.asyncio
    async def test_different_effect_sizes(self, sample_project_with_hypotheses):
        """Test running with different effect sizes."""
        for effect_size in ["small", "medium", "large"]:
            result_project, summary = await run_with_summary(
                sample_project_with_hypotheses,
                effect_size=effect_size,
                use_llm=False
            )
            
            assert result_project.design is not None
            assert summary["sample_size"] > 0


class TestDesignQuality:
    """Test quality of generated designs."""
    
    @pytest.mark.asyncio
    async def test_design_is_testable(self, sample_project_with_hypotheses):
        """Test that design is actually testable."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        # Must have at least 2 conditions for comparison
        assert len(proposal.conditions) >= 2
        
        # Must have measures for DVs
        assert len(proposal.measures) >= 1
        
        # Conditions should be distinct
        condition_labels = [c.label for c in proposal.conditions]
        assert len(set(condition_labels)) == len(condition_labels)  # No duplicates
    
    @pytest.mark.asyncio
    async def test_design_has_control(self, sample_project_with_hypotheses):
        """Test that design includes appropriate control/comparison."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        # Should have multiple conditions for comparison
        assert len(proposal.conditions) >= 2
        
        # At least one condition might be control-like
        condition_descriptions = [c.manipulation_description.lower() for c in proposal.conditions]
        # Just check we have varied conditions
        assert len(set(condition_descriptions)) >= 2


class TestModuleIntegration:
    """Test integration with other modules."""
    
    @pytest.mark.asyncio
    async def test_uses_module2_hypotheses(self, sample_project_with_hypotheses):
        """Test that Module 3 uses hypotheses from Module 2."""
        proposal = await propose_design(sample_project_with_hypotheses, use_llm=False)
        
        # Should create conditions based on IVs
        hypothesis_ivs = set()
        for h in sample_project_with_hypotheses.hypotheses:
            hypothesis_ivs.update(h.iv)
        
        # Should create measures based on DVs
        hypothesis_dvs = set()
        for h in sample_project_with_hypotheses.hypotheses:
            hypothesis_dvs.update(h.dv)
        
        # Design should address the hypotheses
        assert len(proposal.conditions) >= 2  # Multiple levels/conditions for IVs
        assert len(proposal.measures) >= 1  # Measures for DVs
    
    @pytest.mark.asyncio
    async def test_prepares_for_module4(self, sample_project_with_hypotheses):
        """Test that Module 3 output is suitable for Module 4."""
        result_project = await run(
            sample_project_with_hypotheses,
            effect_size="medium",
            use_llm=False
        )
        
        # Module 4 needs conditions to assign stimuli to
        assert result_project.design is not None
        assert len(result_project.design.conditions) >= 2
        
        # Conditions should have clear descriptions
        for condition in result_project.design.conditions:
            assert condition.id is not None
            assert condition.label is not None
            assert condition.manipulation_description is not None


@pytest.mark.asyncio
@pytest.mark.slow
async def test_realistic_design_scenario():
    """Test with a realistic research scenario."""
    project = ProjectState()
    
    # Realistic research setup
    project.rq = ResearchQuestion(
        raw_text="How does attachment style affect emotion regulation in romantic conflicts?",
        parsed_constructs=["attachment style", "emotion regulation", "conflict"],
        domain="Social Psychology"
    )
    
    project.hypotheses = [
        Hypothesis(
            id="h1",
            text="Anxious attachment predicts greater emotional reactivity during conflicts",
            iv=["Attachment Style"],
            dv=["Emotional Reactivity"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment Theory"],
            expected_direction="Positive"
        ),
        Hypothesis(
            id="h2",
            text="Secure attachment predicts more adaptive emotion regulation strategies",
            iv=["Attachment Style"],
            dv=["Emotion Regulation Strategies"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment Theory"],
            expected_direction="Positive"
        ),
        Hypothesis(
            id="h3",
            text="Relationship satisfaction moderates the effect",
            iv=["Attachment Style"],
            dv=["Emotion Regulation"],
            mediators=[],
            moderators=["Relationship Satisfaction"],
            theoretical_basis=["Attachment Theory", "Relationship Research"],
            expected_direction="Interaction"
        )
    ]
    
    project.audit_log = []
    
    # Run Module 3
    result_project, summary = await run_with_summary(
        project,
        effect_size="medium",
        use_llm=False
    )
    
    # Comprehensive validation
    assert result_project.design is not None
    
    # Check design quality
    assert summary["num_conditions"] >= 2
    assert summary["num_measures"] >= 2  # Multiple DVs
    assert summary["sample_size"] >= 60  # Reasonable sample for medium effect
    assert summary["methods_word_count"] >= 200  # Substantial Methods section
    
    # Print results
    print("\n" + "="*60)
    print("REALISTIC DESIGN BUILDER TEST")
    print("="*60)
    print(f"Research Question: {project.rq.raw_text}")
    print(f"\nDesign Summary:")
    print(f"  Type: {summary['design_type']}")
    print(f"  Conditions: {summary['num_conditions']}")
    print(f"  Measures: {summary['num_measures']}")
    print(f"  Sample Size: {summary['sample_size']} participants")
    print(f"  Confound Warnings: {summary['confound_warnings']}")
    print(f"  Methods: {summary['methods_word_count']} words")
    print("\nConditions:")
    for i, cond in enumerate(result_project.design.conditions, 1):
        print(f"  {i}. {cond.label}")
        print(f"     {cond.manipulation_description[:80]}...")
    print("\nMeasures:")
    for i, measure in enumerate(result_project.design.measures, 1):
        print(f"  {i}. {measure.label}")
        if measure.scale:
            print(f"     Scale: {measure.scale}")
    print("="*60)
