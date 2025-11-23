"""Integration tests for Hypothesis Generator & Structurer (Module 2).

Tests the integration of all hypothesis generation components:
- Hypothesis generation from concepts
- Hypothesis validation
- Export functionality
- Complete module workflow
"""

import pytest
import asyncio
from typing import List

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    ConceptNode,
    ConceptEdge,
    Hypothesis,
    AuditEntry
)

from Hypothesis_Generator_Structurer import run, run_with_summary
from Hypothesis_Generator_Structurer.hypothesis_generator import (
    generate_hypotheses,
    HypothesisGenerationError
)
from Hypothesis_Generator_Structurer.hypothesis_validator import (
    validate_hypotheses,
    ValidationResult
)
from Hypothesis_Generator_Structurer.hypothesis_exporter import (
    export_to_json,
    export_to_markdown_table,
    generate_hypothesis_report
)


@pytest.fixture
def sample_project():
    """Create a sample project with research question and concepts."""
    project = ProjectState()
    
    project.rq = ResearchQuestion(
        raw_text="How does attachment anxiety influence emotion regulation strategies in romantic relationships?",
        parsed_constructs=["attachment anxiety", "emotion regulation", "romantic relationships"],
        domain="Social Psychology"
    )
    
    project.concepts = {
        "nodes": [
            ConceptNode(
                id="c1",
                label="Attachment Anxiety",
                type="construct",
                common_measures=["ECR-R Anxiety subscale", "ASQ"]
            ),
            ConceptNode(
                id="c2",
                label="Emotion Regulation",
                type="construct",
                common_measures=["ERQ", "DERS"]
            ),
            ConceptNode(
                id="c3",
                label="Self-Compassion",
                type="construct",
                common_measures=["SCS", "SCS-SF"]
            )
        ],
        "edges": [
            ConceptEdge(
                source="c1",
                target="c2",
                relation_type="predicts"
            ),
            ConceptEdge(
                source="c3",
                target="c2",
                relation_type="moderates"
            )
        ]
    }
    
    project.audit_log = []
    
    return project


class TestHypothesisGeneration:
    """Test hypothesis generation component."""
    
    @pytest.mark.asyncio
    async def test_generate_hypotheses_basic(self, sample_project):
        """Test basic hypothesis generation."""
        result = await generate_hypotheses(sample_project, num_hypotheses=3)
        
        # Check structure
        assert result.hypotheses is not None
        assert len(result.hypotheses) > 0
        assert result.summary is not None
        
        # Check each hypothesis has required fields
        for h in result.hypotheses:
            assert h.id is not None
            assert h.text is not None
            assert len(h.iv) > 0  # At least one IV
            assert len(h.dv) > 0  # At least one DV
            assert h.expected_direction is not None
    
    @pytest.mark.asyncio
    async def test_generate_multiple_hypotheses(self, sample_project):
        """Test generating multiple hypotheses."""
        for n in [1, 3, 5]:
            result = await generate_hypotheses(sample_project, num_hypotheses=n)
            assert len(result.hypotheses) >= n * 0.8  # Allow some flexibility
    
    @pytest.mark.asyncio
    async def test_hypotheses_use_constructs(self, sample_project):
        """Test that hypotheses use constructs from concepts."""
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        
        # Collect all variables from hypotheses
        all_vars = set()
        for h in result.hypotheses:
            all_vars.update(h.iv)
            all_vars.update(h.dv)
            all_vars.update(h.mediators)
            all_vars.update(h.moderators)
        
        # Check that some constructs from concepts appear
        concept_labels = {node.label.lower() for node in sample_project.concepts["nodes"]}
        var_labels = {v.lower() for v in all_vars}
        
        # At least some overlap expected
        overlap = concept_labels.intersection(var_labels)
        assert len(overlap) > 0
    
    @pytest.mark.asyncio
    async def test_generation_without_concepts(self):
        """Test hypothesis generation without concept graph."""
        project = ProjectState()
        project.rq = ResearchQuestion(
            raw_text="Does stress affect cognitive performance?",
            parsed_constructs=["stress", "cognitive performance"],
            domain="Cognitive Psychology"
        )
        project.concepts = {"nodes": [], "edges": []}
        project.audit_log = []
        
        # Should still generate hypotheses from RQ
        result = await generate_hypotheses(project, num_hypotheses=3)
        assert len(result.hypotheses) > 0


class TestHypothesisValidation:
    """Test hypothesis validation component."""
    
    def test_validate_valid_hypotheses(self):
        """Test validation of well-formed hypotheses."""
        hypotheses = [
            Hypothesis(
                id="h1",
                text="Attachment anxiety predicts maladaptive emotion regulation",
                iv=["Attachment Anxiety"],
                dv=["Emotion Regulation Strategies"],
                mediators=[],
                moderators=[],
                theoretical_basis=["Attachment Theory"],
                expected_direction="Positive: Higher attachment anxiety leads to more maladaptive strategies"
            ),
            Hypothesis(
                id="h2",
                text="Self-compassion moderates the relationship",
                iv=["Attachment Anxiety"],
                dv=["Emotion Regulation"],
                mediators=[],
                moderators=["Self-Compassion"],
                theoretical_basis=["Attachment Theory", "Self-Compassion Research"],
                expected_direction="Interaction: Self-compassion buffers the effect"
            )
        ]
        
        results = validate_hypotheses(hypotheses)
        
        assert len(results) == 2
        for result in results:
            assert result.is_valid is True
            assert result.score >= 0.7  # Good quality
            assert len(result.warnings) == 0
    
    def test_validate_invalid_hypotheses(self):
        """Test validation catches invalid hypotheses."""
        # Missing DV
        invalid_h1 = Hypothesis(
            id="h_invalid",
            text="Attachment anxiety is important",
            iv=["Attachment Anxiety"],
            dv=[],  # Missing DV
            mediators=[],
            moderators=[],
            theoretical_basis=[],
            expected_direction=""
        )
        
        results = validate_hypotheses([invalid_h1])
        assert len(results) == 1
        assert results[0].is_valid is False
        assert len(results[0].warnings) > 0
    
    @pytest.mark.asyncio
    async def test_validation_scoring(self, sample_project):
        """Test that validation scores hypotheses appropriately."""
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        validation_results = validate_hypotheses(result.hypotheses)
        
        # All should have scores
        for vr in validation_results:
            assert 0.0 <= vr.score <= 1.0
        
        # Average score should be reasonable
        avg_score = sum(vr.score for vr in validation_results) / len(validation_results)
        assert avg_score >= 0.5  # At least moderate quality


class TestHypothesisExport:
    """Test hypothesis export functionality."""
    
    @pytest.mark.asyncio
    async def test_export_to_json(self, sample_project):
        """Test JSON export."""
        result = await generate_hypotheses(sample_project, num_hypotheses=3)
        
        json_output = export_to_json(result.hypotheses)
        
        assert json_output is not None
        assert len(json_output) > 0
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)
        assert len(parsed) == len(result.hypotheses)
    
    @pytest.mark.asyncio
    async def test_export_to_markdown(self, sample_project):
        """Test markdown table export."""
        result = await generate_hypotheses(sample_project, num_hypotheses=3)
        
        markdown = export_to_markdown_table(result.hypotheses)
        
        assert markdown is not None
        assert len(markdown) > 0
        assert "|" in markdown  # Table format
        assert "IV" in markdown
        assert "DV" in markdown
    
    @pytest.mark.asyncio
    async def test_generate_full_report(self, sample_project):
        """Test full report generation."""
        result = await generate_hypotheses(sample_project, num_hypotheses=3)
        validation_results = validate_hypotheses(result.hypotheses)
        
        report = generate_hypothesis_report(
            result.hypotheses,
            validation_results,
            result.summary
        )
        
        assert report is not None
        assert len(report) > 0
        # Report should contain key sections
        assert "Hypothesis" in report or "hypothesis" in report
        assert "Valid" in report or "valid" in report


class TestCompleteModule:
    """Test complete Module 2 workflow."""
    
    @pytest.mark.asyncio
    async def test_full_module_run(self, sample_project):
        """Test running complete Module 2."""
        result_project = await run(sample_project, num_hypotheses=3)
        
        # Check project was updated
        assert result_project.hypotheses is not None
        assert len(result_project.hypotheses) > 0
        
        # Check audit log updated
        assert len(result_project.audit_log) > 0
        
        # Check for success entries
        success_entries = [
            e for e in result_project.audit_log
            if "complete" in e.message.lower() or "generated" in e.message.lower()
        ]
        assert len(success_entries) > 0
    
    @pytest.mark.asyncio
    async def test_run_with_summary(self, sample_project):
        """Test run_with_summary function."""
        result_project, summary = await run_with_summary(sample_project, num_hypotheses=3)
        
        # Check project updated
        assert result_project.hypotheses is not None
        
        # Check summary structure
        assert "num_hypotheses" in summary
        assert "validated" in summary
        assert "unique_ivs" in summary
        assert "unique_dvs" in summary
        assert summary["num_hypotheses"] > 0
    
    @pytest.mark.asyncio
    async def test_module_error_handling_no_rq(self):
        """Test error handling when research question missing."""
        project = ProjectState()
        project.rq = None
        project.audit_log = []
        
        with pytest.raises(Exception):  # Should raise Module2Error
            await run(project)
    
    @pytest.mark.asyncio
    async def test_module_error_handling_no_constructs(self):
        """Test error handling when constructs missing."""
        project = ProjectState()
        project.rq = ResearchQuestion(
            raw_text="Test question",
            parsed_constructs=[],  # No constructs
            domain="Test"
        )
        project.audit_log = []
        
        with pytest.raises(Exception):  # Should raise Module2Error
            await run(project)


class TestHypothesisQuality:
    """Test quality of generated hypotheses."""
    
    @pytest.mark.asyncio
    async def test_hypotheses_have_all_roles(self, sample_project):
        """Test that hypotheses properly identify variable roles."""
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        
        # At least some hypotheses should have mediators or moderators
        has_mediators = any(len(h.mediators) > 0 for h in result.hypotheses)
        has_moderators = any(len(h.moderators) > 0 for h in result.hypotheses)
        
        # Given the sample project has moderation relationship
        assert has_mediators or has_moderators
    
    @pytest.mark.asyncio
    async def test_hypotheses_testability(self, sample_project):
        """Test that hypotheses are testable (have clear IV/DV)."""
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        
        for h in result.hypotheses:
            # Each hypothesis must be testable
            assert len(h.iv) > 0, f"Hypothesis {h.id} has no IV"
            assert len(h.dv) > 0, f"Hypothesis {h.id} has no DV"
            assert len(h.expected_direction) > 0, f"Hypothesis {h.id} has no direction"
    
    @pytest.mark.asyncio
    async def test_hypotheses_diversity(self, sample_project):
        """Test that multiple hypotheses are diverse."""
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        
        # Check that hypotheses are not identical
        hypothesis_texts = [h.text for h in result.hypotheses]
        unique_texts = set(hypothesis_texts)
        
        # Should have at least 80% unique hypotheses
        assert len(unique_texts) >= len(hypothesis_texts) * 0.8
    
    @pytest.mark.asyncio
    async def test_theoretical_grounding(self, sample_project):
        """Test that hypotheses reference theoretical basis."""
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        
        # At least some hypotheses should have theoretical basis
        with_theory = sum(1 for h in result.hypotheses if len(h.theoretical_basis) > 0)
        assert with_theory >= len(result.hypotheses) * 0.5  # At least 50%


class TestModuleIntegration:
    """Test integration with other modules."""
    
    @pytest.mark.asyncio
    async def test_uses_module1_concepts(self, sample_project):
        """Test that Module 2 uses concepts from Module 1."""
        # Module 1 provides concept graph
        result = await generate_hypotheses(sample_project, num_hypotheses=5)
        
        # Should reference concepts from Module 1
        concept_labels = {node.label for node in sample_project.concepts["nodes"]}
        
        # Check if any hypothesis variables match concepts
        hypothesis_vars = set()
        for h in result.hypotheses:
            hypothesis_vars.update(h.iv)
            hypothesis_vars.update(h.dv)
        
        # Normalize for comparison
        concept_labels_lower = {c.lower() for c in concept_labels}
        hypothesis_vars_lower = {v.lower() for v in hypothesis_vars}
        
        overlap = concept_labels_lower.intersection(hypothesis_vars_lower)
        assert len(overlap) > 0  # Should use at least some concepts
    
    @pytest.mark.asyncio
    async def test_prepares_for_module3(self, sample_project):
        """Test that Module 2 output is suitable for Module 3."""
        result_project = await run(sample_project, num_hypotheses=3)
        
        # Module 3 needs hypotheses with clear variables
        assert result_project.hypotheses is not None
        assert len(result_project.hypotheses) > 0
        
        # Each hypothesis should be actionable for design
        for h in result_project.hypotheses:
            assert len(h.iv) > 0  # Module 3 needs IVs to create conditions
            assert len(h.dv) > 0  # Module 3 needs DVs to create measures


@pytest.mark.asyncio
@pytest.mark.slow
async def test_realistic_research_scenario():
    """Test with a realistic research scenario."""
    project = ProjectState()
    
    # Realistic psychology research question
    project.rq = ResearchQuestion(
        raw_text=(
            "This study examines the relationship between parental attachment style "
            "and children's emotion regulation abilities, with empathy as a potential "
            "mediating factor. We hypothesize that secure parental attachment predicts "
            "better emotion regulation in children, and this effect is mediated by "
            "the child's level of empathy."
        ),
        parsed_constructs=["attachment style", "emotion regulation", "empathy", "parental relationships"],
        domain="Developmental Psychology"
    )
    
    # Rich concept graph from Module 1
    project.concepts = {
        "nodes": [
            ConceptNode(id="c1", label="Parental Attachment", type="construct", 
                       common_measures=["PAQ", "IPPA"]),
            ConceptNode(id="c2", label="Child Emotion Regulation", type="construct",
                       common_measures=["ERC", "DERS-C"]),
            ConceptNode(id="c3", label="Empathy", type="construct",
                       common_measures=["IRI-C", "BEES"]),
            ConceptNode(id="c4", label="Secure Attachment", type="construct",
                       common_measures=["Attachment Q-Set"]),
        ],
        "edges": [
            ConceptEdge(source="c1", target="c2", relation_type="predicts"),
            ConceptEdge(source="c3", target="c2", relation_type="mediates"),
            ConceptEdge(source="c1", target="c3", relation_type="associated_with"),
        ]
    }
    
    project.audit_log = []
    
    # Run Module 2
    result_project, summary = await run_with_summary(project, num_hypotheses=5)
    
    # Comprehensive validation
    assert result_project.hypotheses is not None
    assert len(result_project.hypotheses) >= 3
    
    # Check quality
    validation_results = validate_hypotheses(result_project.hypotheses)
    valid_count = sum(1 for vr in validation_results if vr.is_valid)
    assert valid_count >= 2  # At least 2 valid hypotheses
    
    # Check variable diversity
    assert summary["unique_ivs"] >= 2
    assert summary["unique_dvs"] >= 1
    
    # Check for mediation hypothesis (given concept graph)
    has_mediation = any(len(h.mediators) > 0 for h in result_project.hypotheses)
    assert has_mediation  # Should propose mediation based on concept edges
    
    # Print results for inspection
    print("\n" + "="*60)
    print("REALISTIC HYPOTHESIS GENERATION TEST")
    print("="*60)
    print(f"Research Question: {project.rq.raw_text[:100]}...")
    print(f"\nGenerated {summary['num_hypotheses']} hypotheses:")
    print(f"  Valid: {summary['validated']}/{summary['num_hypotheses']}")
    print(f"  Unique IVs: {summary['unique_ivs']}")
    print(f"  Unique DVs: {summary['unique_dvs']}")
    print(f"  With mediators: {summary['with_mediators']}")
    print(f"  With moderators: {summary['with_moderators']}")
    print(f"\nSample Hypotheses:")
    for i, h in enumerate(result_project.hypotheses[:3], 1):
        print(f"\n{i}. {h.text}")
        print(f"   IV: {', '.join(h.iv)}")
        print(f"   DV: {', '.join(h.dv)}")
        if h.mediators:
            print(f"   Mediators: {', '.join(h.mediators)}")
        if h.moderators:
            print(f"   Moderators: {', '.join(h.moderators)}")
    print("="*60)
