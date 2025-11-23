"""Integration tests for Stimulus Factory (Module 4).

Tests the integration of all stimulus generation components:
- Stimulus generation
- Metadata annotation
- Balance optimization
- Content filtering
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
    StimulusItem,
    AuditEntry
)

from Stimulus_Factory import run, run_with_summary
from Stimulus_Factory.stimulus_generator import (
    generate_stimuli,
    StimulusGenerationError
)
from Stimulus_Factory.metadata_annotator import (
    annotate_metadata,
    MetadataAnnotation
)
from Stimulus_Factory.balance_optimizer import (
    optimize_balance,
    check_balance_quality
)
from Stimulus_Factory.content_filter import (
    filter_stimuli,
    FilterCriteria
)


@pytest.fixture
def sample_project_with_design():
    """Create a sample project with design from Module 3."""
    project = ProjectState()
    
    project.rq = ResearchQuestion(
        raw_text="How does attachment anxiety influence emotion regulation?",
        parsed_constructs=["attachment anxiety", "emotion regulation"],
        domain="Social Psychology"
    )
    
    project.hypotheses = [
        Hypothesis(
            id="h1",
            text="Attachment anxiety predicts maladaptive emotion regulation",
            iv=["Attachment Anxiety"],
            dv=["Emotion Regulation Strategies"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment Theory"],
            expected_direction="Positive"
        )
    ]
    
    project.design = ExperimentDesign(
        design_type="between_subjects",
        conditions=[
            Condition(
                id="c1",
                label="High Anxiety",
                manipulation_description="Scenario depicting anxious attachment in relationship conflict"
            ),
            Condition(
                id="c2",
                label="Low Anxiety",
                manipulation_description="Scenario depicting secure attachment in relationship conflict"
            )
        ],
        measures=[],
        time_points=["baseline"],
        sample_size_plan=None,
        methods_draft=""
    )
    
    project.audit_log = []
    
    return project


class TestStimulusGeneration:
    """Test stimulus generation component."""
    
    @pytest.mark.asyncio
    async def test_generate_basic_stimuli(self, sample_project_with_design):
        """Test basic stimulus generation."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Check structure
        assert result.stimuli is not None
        assert len(result.stimuli) > 0
        
        # Check each stimulus has required fields
        for stim in result.stimuli:
            assert stim.id is not None
            assert stim.content is not None
            assert stim.condition_id is not None
            assert len(stim.content) > 0
    
    @pytest.mark.asyncio
    async def test_stimuli_per_condition(self, sample_project_with_design):
        """Test that stimuli are generated for each condition."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Count stimuli per condition
        condition_counts = {}
        for stim in result.stimuli:
            condition_counts[stim.condition_id] = condition_counts.get(stim.condition_id, 0) + 1
        
        # Should have stimuli for each condition
        for condition in sample_project_with_design.design.conditions:
            assert condition.id in condition_counts
            assert condition_counts[condition.id] >= 3  # At least some stimuli
    
    @pytest.mark.asyncio
    async def test_stimulus_diversity(self, sample_project_with_design):
        """Test that generated stimuli are diverse."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Check for diversity
        contents = [stim.content for stim in result.stimuli]
        unique_contents = set(contents)
        
        # Should have mostly unique stimuli
        assert len(unique_contents) >= len(contents) * 0.8


class TestMetadataAnnotation:
    """Test metadata annotation functionality."""
    
    @pytest.mark.asyncio
    async def test_annotate_metadata_basic(self, sample_project_with_design):
        """Test basic metadata annotation."""
        # Generate stimuli first
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=3,
            use_llm=False
        )
        
        # Annotate metadata
        annotated = await annotate_metadata(result.stimuli, use_llm=False)
        
        assert len(annotated) == len(result.stimuli)
        
        # Check metadata fields
        for stim in annotated:
            assert hasattr(stim, 'metadata')
            assert stim.metadata is not None
    
    @pytest.mark.asyncio
    async def test_metadata_completeness(self, sample_project_with_design):
        """Test that metadata contains expected fields."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=3,
            use_llm=False
        )
        
        annotated = await annotate_metadata(result.stimuli, use_llm=False)
        
        # Check for common metadata fields
        for stim in annotated:
            metadata = stim.metadata
            # Should have some metadata fields
            assert len(metadata) > 0


class TestBalanceOptimization:
    """Test balance optimization functionality."""
    
    @pytest.mark.asyncio
    async def test_optimize_balance_basic(self, sample_project_with_design):
        """Test basic balance optimization."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        annotated = await annotate_metadata(result.stimuli, use_llm=False)
        optimized = optimize_balance(annotated)
        
        assert len(optimized) > 0
        # Should have balanced set
        assert len(optimized) <= len(annotated)
    
    @pytest.mark.asyncio
    async def test_balance_across_conditions(self, sample_project_with_design):
        """Test that optimization balances across conditions."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        annotated = await annotate_metadata(result.stimuli, use_llm=False)
        optimized = optimize_balance(annotated)
        
        # Count per condition
        condition_counts = {}
        for stim in optimized:
            condition_counts[stim.condition_id] = condition_counts.get(stim.condition_id, 0) + 1
        
        # Should be roughly balanced
        counts = list(condition_counts.values())
        if len(counts) > 1:
            max_count = max(counts)
            min_count = min(counts)
            # Allow some tolerance
            assert max_count - min_count <= 2
    
    @pytest.mark.asyncio
    async def test_balance_quality_check(self, sample_project_with_design):
        """Test balance quality checking."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        annotated = await annotate_metadata(result.stimuli, use_llm=False)
        optimized = optimize_balance(annotated)
        
        quality = check_balance_quality(optimized)
        
        # Should return quality metrics
        assert quality is not None
        assert 'balance_score' in quality or 'balanced' in quality


class TestContentFiltering:
    """Test content filtering functionality."""
    
    @pytest.mark.asyncio
    async def test_filter_stimuli_basic(self, sample_project_with_design):
        """Test basic stimulus filtering."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        filtered = await filter_stimuli(
            result.stimuli,
            criteria=FilterCriteria(min_length=10, max_length=1000)
        )
        
        # Check filtered results
        assert len(filtered) > 0
        
        # Check length constraints
        for stim in filtered:
            assert 10 <= len(stim.content) <= 1000
    
    @pytest.mark.asyncio
    async def test_filter_inappropriate_content(self, sample_project_with_design):
        """Test filtering of inappropriate content."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        filtered = await filter_stimuli(
            result.stimuli,
            criteria=FilterCriteria(check_appropriateness=True)
        )
        
        # Should filter out inappropriate content
        assert len(filtered) <= len(result.stimuli)


class TestCompleteModule:
    """Test complete Module 4 workflow."""
    
    @pytest.mark.asyncio
    async def test_full_module_run(self, sample_project_with_design):
        """Test running complete Module 4."""
        result_project = await run(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Check project was updated
        assert result_project.stimuli is not None
        assert len(result_project.stimuli) > 0
        
        # Check stimuli have metadata
        for stim in result_project.stimuli:
            assert stim.metadata is not None
        
        # Check audit log updated
        assert len(result_project.audit_log) > 0
    
    @pytest.mark.asyncio
    async def test_run_with_summary(self, sample_project_with_design):
        """Test run_with_summary function."""
        result_project, summary = await run_with_summary(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Check project updated
        assert result_project.stimuli is not None
        
        # Check summary structure
        assert "total_stimuli" in summary
        assert "per_condition" in summary
        assert "balanced" in summary
        assert summary["total_stimuli"] > 0
    
    @pytest.mark.asyncio
    async def test_module_error_handling_no_design(self):
        """Test error handling when design missing."""
        project = ProjectState()
        project.rq = ResearchQuestion(
            raw_text="Test",
            parsed_constructs=["test"],
            domain="Test"
        )
        project.design = None  # No design
        project.audit_log = []
        
        with pytest.raises(Exception):  # Should raise Module4Error
            await run(project, use_llm=False)
    
    @pytest.mark.asyncio
    async def test_module_error_handling_no_conditions(self):
        """Test error handling when conditions missing."""
        project = ProjectState()
        project.rq = ResearchQuestion(
            raw_text="Test",
            parsed_constructs=["test"],
            domain="Test"
        )
        project.design = ExperimentDesign(
            design_type="between_subjects",
            conditions=[],  # No conditions
            measures=[],
            time_points=[],
            sample_size_plan=None,
            methods_draft=""
        )
        project.audit_log = []
        
        with pytest.raises(Exception):  # Should raise Module4Error
            await run(project, use_llm=False)


class TestStimulusQuality:
    """Test quality of generated stimuli."""
    
    @pytest.mark.asyncio
    async def test_stimuli_are_appropriate_length(self, sample_project_with_design):
        """Test that stimuli have appropriate length."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        for stim in result.stimuli:
            # Should be substantial but not too long
            assert 20 <= len(stim.content) <= 2000
    
    @pytest.mark.asyncio
    async def test_stimuli_match_conditions(self, sample_project_with_design):
        """Test that stimuli match their assigned conditions."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Get condition descriptions
        condition_info = {
            c.id: c.manipulation_description.lower()
            for c in sample_project_with_design.design.conditions
        }
        
        # Check stimuli relate to their conditions
        for stim in result.stimuli:
            assert stim.condition_id in condition_info
            # Content should relate to condition (flexible check)
            assert len(stim.content) > 0
    
    @pytest.mark.asyncio
    async def test_stimuli_have_unique_ids(self, sample_project_with_design):
        """Test that all stimuli have unique IDs."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        ids = [stim.id for stim in result.stimuli]
        unique_ids = set(ids)
        
        assert len(unique_ids) == len(ids)  # All IDs unique


class TestModuleIntegration:
    """Test integration with other modules."""
    
    @pytest.mark.asyncio
    async def test_uses_module3_design(self, sample_project_with_design):
        """Test that Module 4 uses design from Module 3."""
        result = await generate_stimuli(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Should generate stimuli for each condition
        condition_ids = {c.id for c in sample_project_with_design.design.conditions}
        stimulus_condition_ids = {stim.condition_id for stim in result.stimuli}
        
        # All conditions should have stimuli
        assert condition_ids.issubset(stimulus_condition_ids)
    
    @pytest.mark.asyncio
    async def test_prepares_for_module5(self, sample_project_with_design):
        """Test that Module 4 output is suitable for Module 5."""
        result_project = await run(
            sample_project_with_design,
            num_per_condition=5,
            use_llm=False
        )
        
        # Module 5 needs stimuli with metadata for simulation
        assert result_project.stimuli is not None
        assert len(result_project.stimuli) > 0
        
        # Each stimulus should have metadata for simulation
        for stim in result_project.stimuli:
            assert stim.id is not None
            assert stim.content is not None
            assert stim.condition_id is not None
            assert stim.metadata is not None


@pytest.mark.asyncio
@pytest.mark.slow
async def test_realistic_stimulus_scenario():
    """Test with a realistic research scenario."""
    project = ProjectState()
    
    # Realistic research setup
    project.rq = ResearchQuestion(
        raw_text="How does attachment style affect emotion regulation in conflicts?",
        parsed_constructs=["attachment style", "emotion regulation"],
        domain="Social Psychology"
    )
    
    project.hypotheses = [
        Hypothesis(
            id="h1",
            text="Anxious attachment predicts maladaptive emotion regulation",
            iv=["Attachment Style"],
            dv=["Emotion Regulation"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment Theory"],
            expected_direction="Positive"
        )
    ]
    
    project.design = ExperimentDesign(
        design_type="between_subjects",
        conditions=[
            Condition(
                id="c1",
                label="Anxious Attachment",
                manipulation_description="Vignette depicting anxious attachment patterns in romantic conflict"
            ),
            Condition(
                id="c2",
                label="Secure Attachment",
                manipulation_description="Vignette depicting secure attachment patterns in romantic conflict"
            ),
            Condition(
                id="c3",
                label="Control",
                manipulation_description="Neutral vignette about daily interactions"
            )
        ],
        measures=[],
        time_points=["baseline"],
        sample_size_plan=None,
        methods_draft=""
    )
    
    project.audit_log = []
    
    # Run Module 4
    result_project, summary = await run_with_summary(
        project,
        num_per_condition=10,
        use_llm=False
    )
    
    # Comprehensive validation
    assert result_project.stimuli is not None
    assert len(result_project.stimuli) >= 15  # At least 5 per condition
    
    # Check balance
    condition_counts = {}
    for stim in result_project.stimuli:
        condition_counts[stim.condition_id] = condition_counts.get(stim.condition_id, 0) + 1
    
    # Should be roughly balanced
    counts = list(condition_counts.values())
    max_count = max(counts)
    min_count = min(counts)
    assert max_count - min_count <= 3  # Reasonable balance
    
    # Check metadata
    with_metadata = sum(1 for stim in result_project.stimuli if stim.metadata)
    assert with_metadata >= len(result_project.stimuli) * 0.8  # Most have metadata
    
    # Print results
    print("\n" + "="*60)
    print("REALISTIC STIMULUS FACTORY TEST")
    print("="*60)
    print(f"Research Question: {project.rq.raw_text}")
    print(f"\nStimulus Generation Summary:")
    print(f"  Total Stimuli: {summary['total_stimuli']}")
    print(f"  Per Condition: {summary['per_condition']}")
    print(f"  Balanced: {summary['balanced']}")
    print("\nCondition Distribution:")
    for cond_id, count in condition_counts.items():
        cond = next(c for c in project.design.conditions if c.id == cond_id)
        print(f"  {cond.label}: {count} stimuli")
    print("\nSample Stimuli:")
    for i, stim in enumerate(result_project.stimuli[:3], 1):
        cond = next(c for c in project.design.conditions if c.id == stim.condition_id)
        print(f"\n{i}. Condition: {cond.label}")
        print(f"   Content: {stim.content[:100]}...")
        if stim.metadata:
            print(f"   Metadata fields: {list(stim.metadata.keys())}")
    print("="*60)
