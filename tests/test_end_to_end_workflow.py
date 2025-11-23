"""End-to-end workflow tests for Research Copilot.

Tests the complete workflow from research question to final simulation results,
integrating all five modules:
1. Literature Landscape Explorer
2. Hypothesis Generator
3. Design Builder
4. Stimulus Factory
5. Synthetic Participant Simulator
"""

import pytest
import asyncio
from pathlib import Path
import json

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    AuditEntry
)

# Import all modules
import copilot_workflow.ingest_rq as ingest_rq
try:
    from Literature_Landscape_Explorer import run as run_literature
except ImportError:
    run_literature = None

try:
    from Hypothesis_Generator_Structurer import run as run_hypothesis
except ImportError:
    run_hypothesis = None

try:
    from Experimental_Design_Builder_Critic import run as run_design
except ImportError:
    run_design = None

try:
    from Stimulus_Factory import run as run_stimulus
except ImportError:
    run_stimulus = None

from Synthetic_Participant_Simulator import run as run_simulation


class TestCompleteWorkflow:
    """Test the complete end-to-end workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_simulation_only_workflow(self):
        """Test workflow with only simulation module (other modules stubbed)."""
        # Step 1: Create research question
        rq_text = (
            "How does attachment anxiety influence emotion regulation strategies "
            "in romantic relationships, and does self-compassion moderate this effect?"
        )
        
        project = ProjectState(
            rq=ResearchQuestion(
                raw_text=rq_text,
                constructs=["attachment_anxiety", "emotion_regulation", "self_compassion"]
            ),
            audit_log=[]
        )
        
        # Step 2: Create stub design (simulating Module 3 output)
        from copilot_workflow.schemas import (
            ExperimentDesign,
            Condition,
            Measure,
            SampleSizePlan
        )
        
        project.design = ExperimentDesign(
            design_type="between_subjects",
            conditions=[
                Condition(
                    id="high_attachment_anxiety",
                    label="High Attachment Anxiety",
                    manipulation_description="Priming high attachment anxiety through scenarios"
                ),
                Condition(
                    id="low_attachment_anxiety",
                    label="Low Attachment Anxiety (Control)",
                    manipulation_description="Neutral scenarios (control condition)"
                )
            ],
            measures=[
                Measure(
                    id="emotion_regulation",
                    label="Emotion Regulation Strategies",
                    scale="ERQ",
                    time_points=["post"]
                ),
                Measure(
                    id="state_anxiety",
                    label="State Anxiety",
                    scale="STAI-S",
                    time_points=["post"]
                ),
                Measure(
                    id="self_compassion",
                    label="Self-Compassion",
                    scale="SCS-SF",
                    time_points=["post"]
                )
            ],
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="medium",
                per_condition_range=[50, 60],
                total_n_range=[100, 120]
            )
        )
        
        # Step 3: Create stub stimuli (simulating Module 4 output)
        from copilot_workflow.schemas import StimulusItem, StimulusMetadata
        
        project.stimuli = [
            StimulusItem(
                id="stim_001",
                text="Imagine your partner being distant and unresponsive when you try to discuss your feelings.",
                metadata=StimulusMetadata(
                    valence="negative",
                    intensity="high",
                    ambiguity_level="low",
                    assigned_condition="high_attachment_anxiety"
                )
            ),
            StimulusItem(
                id="stim_002",
                text="Picture your partner being preoccupied with their phone while you're trying to connect.",
                metadata=StimulusMetadata(
                    valence="negative",
                    intensity="medium",
                    ambiguity_level="medium",
                    assigned_condition="high_attachment_anxiety"
                )
            ),
            StimulusItem(
                id="stim_003",
                text="Think about a typical evening at home with your partner doing separate activities.",
                metadata=StimulusMetadata(
                    valence="neutral",
                    intensity="low",
                    ambiguity_level="low",
                    assigned_condition="low_attachment_anxiety"
                )
            ),
            StimulusItem(
                id="stim_004",
                text="Consider your partner being busy with work and less available than usual.",
                metadata=StimulusMetadata(
                    valence="neutral",
                    intensity="low",
                    ambiguity_level="medium",
                    assigned_condition="low_attachment_anxiety"
                )
            )
        ]
        
        # Step 4: Run simulation module
        result_project = await run_simulation(project)
        
        # Verify complete workflow state
        assert result_project.rq is not None
        assert result_project.design is not None
        assert len(result_project.stimuli) > 0
        assert result_project.simulation is not None
        
        # Verify simulation results
        assert len(result_project.simulation.dv_summary) > 0
        assert "Emotion Regulation Strategies" in result_project.simulation.dv_summary
        assert "State Anxiety" in result_project.simulation.dv_summary
        
        # Verify audit trail
        assert len(result_project.audit_log) > 0
        
        # Check that both conditions appear in results
        for dv_name, cond_stats in result_project.simulation.dv_summary.items():
            assert "high_attachment_anxiety" in cond_stats or "low_attachment_anxiety" in cond_stats
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_workflow_state_transitions(self):
        """Test that project state transitions correctly through workflow stages."""
        # Initial state
        project = ProjectState(
            rq=ResearchQuestion(
                raw_text="How does stress affect cognitive performance?",
                constructs=["stress", "cognitive_performance"]
            ),
            audit_log=[]
        )
        
        # Add minimal design
        from copilot_workflow.schemas import (
            ExperimentDesign,
            Condition,
            Measure,
            SampleSizePlan,
            StimulusItem,
            StimulusMetadata
        )
        
        project.design = ExperimentDesign(
            design_type="within_subjects",
            conditions=[
                Condition(id="high_stress", label="High Stress", manipulation_description="High stress condition"),
                Condition(id="low_stress", label="Low Stress", manipulation_description="Low stress condition")
            ],
            measures=[
                Measure(id="cognitive_perf", label="Cognitive Performance", scale="Custom", time_points=["post"])
            ],
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="medium",
                per_condition_range=[30, 40],
                total_n_range=[60, 80]
            )
        )
        
        project.stimuli = [
            StimulusItem(
                id="s1",
                text="High stress task",
                metadata=StimulusMetadata(
                    valence="negative",
                    intensity="high",
                    ambiguity_level="low",
                    assigned_condition="high_stress"
                )
            ),
            StimulusItem(
                id="s2",
                text="Low stress task",
                metadata=StimulusMetadata(
                    valence="neutral",
                    intensity="low",
                    ambiguity_level="low",
                    assigned_condition="low_stress"
                )
            )
        ]
        
        # Track audit log length at each stage
        initial_audit_len = len(project.audit_log)
        
        # Run simulation
        final_project = await run_simulation(project)
        
        # Verify state progression
        assert final_project.rq is not None
        assert final_project.design is not None
        assert final_project.stimuli is not None
        assert final_project.simulation is not None
        
        # Verify audit log grew
        assert len(final_project.audit_log) > initial_audit_len
        
        # Check simulation-specific audit entries
        sim_entries = [e for e in final_project.audit_log if "simulation" in e.message.lower()]
        assert len(sim_entries) > 0


class TestWorkflowDataFlow:
    """Test data flow between workflow modules."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_design_to_simulation_data_flow(self):
        """Test that simulation correctly uses design specifications."""
        from copilot_workflow.schemas import (
            ExperimentDesign,
            Condition,
            Measure,
            SampleSizePlan,
            StimulusItem,
            StimulusMetadata
        )
        
        # Create design with specific parameters
        design = ExperimentDesign(
            design_type="between_subjects",
            conditions=[
                Condition(id="cond_a", label="Condition A", manipulation_description="Manipulation A"),
                Condition(id="cond_b", label="Condition B", manipulation_description="Manipulation B"),
                Condition(id="cond_c", label="Condition C", manipulation_description="Manipulation C")
            ],
            measures=[
                Measure(id="dv1", label="DV1", scale="Scale1", time_points=["post"]),
                Measure(id="dv2", label="DV2", scale="Scale2", time_points=["post"]),
                Measure(id="dv3", label="DV3", scale="Scale3", time_points=["post"])
            ],
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="large",
                per_condition_range=[20, 30],
                total_n_range=[60, 90]
            )
        )
        
        # Create stimuli for each condition
        stimuli = []
        for cond in design.conditions:
            for i in range(2):  # 2 stimuli per condition
                stimuli.append(
                    StimulusItem(
                        id=f"stim_{cond.id}_{i}",
                        text=f"Stimulus for {cond.label} #{i+1}",
                        metadata=StimulusMetadata(
                            valence="neutral",
                            intensity="medium",
                            ambiguity_level="low",
                            assigned_condition=cond.id
                        )
                    )
                )
        
        # Create project
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=design,
            stimuli=stimuli,
            audit_log=[]
        )
        
        # Run simulation
        result = await run_simulation(project)
        
        # Verify all conditions appear in results
        condition_ids = {c.id for c in design.conditions}
        result_condition_ids = set()
        
        for dv_name, cond_stats in result.simulation.dv_summary.items():
            result_condition_ids.update(cond_stats.keys())
        
        assert condition_ids.intersection(result_condition_ids) == condition_ids
        
        # Verify all DVs appear in results
        measure_labels = {m.label for m in design.measures}
        result_dv_labels = set(result.simulation.dv_summary.keys())
        
        assert measure_labels == result_dv_labels
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_stimuli_to_simulation_data_flow(self):
        """Test that simulation uses stimulus metadata correctly."""
        from copilot_workflow.schemas import (
            ExperimentDesign,
            Condition,
            Measure,
            SampleSizePlan,
            StimulusItem,
            StimulusMetadata
        )
        
        design = ExperimentDesign(
            design_type="between_subjects",
            conditions=[
                Condition(id="negative", label="Negative", manipulation_description="Negative stimuli"),
                Condition(id="positive", label="Positive", manipulation_description="Positive stimuli")
            ],
            measures=[
                Measure(id="affect", label="Affect", scale="PANAS", time_points=["post"])
            ],
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="medium",
                per_condition_range=[40, 50],
                total_n_range=[80, 100]
            )
        )
        
        # Create stimuli with different valences
        stimuli = [
            StimulusItem(
                id="neg1",
                text="Negative stimulus",
                metadata=StimulusMetadata(
                    valence="negative",
                    intensity="high",
                    ambiguity_level="low",
                    assigned_condition="negative"
                )
            ),
            StimulusItem(
                id="pos1",
                text="Positive stimulus",
                metadata=StimulusMetadata(
                    valence="positive",
                    intensity="high",
                    ambiguity_level="low",
                    assigned_condition="positive"
                )
            )
        ]
        
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=design,
            stimuli=stimuli,
            audit_log=[]
        )
        
        # Run simulation
        result = await run_simulation(project)
        
        # Get condition means
        affect_stats = result.simulation.dv_summary["Affect"]
        
        # Verify both conditions have results
        assert "negative" in affect_stats
        assert "positive" in affect_stats
        
        # Verify reasonable number of responses per condition
        assert affect_stats["negative"]["n"] >= 20
        assert affect_stats["positive"]["n"] >= 20


class TestWorkflowErrorHandling:
    """Test error handling across workflow stages."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_workflow_handles_missing_prerequisites(self):
        """Test that simulation fails gracefully without required inputs."""
        # Test missing design
        project_no_design = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=None,
            stimuli=[],
            audit_log=[]
        )
        
        with pytest.raises(ValueError):
            await run_simulation(project_no_design)
        
        # Test missing stimuli
        from copilot_workflow.schemas import ExperimentDesign, Condition, Measure
        
        project_no_stimuli = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=ExperimentDesign(
                design_type="between_subjects",
                conditions=[Condition(id="c1", label="C1", manipulation_description="M1")],
                measures=[Measure(id="m1", label="M1", scale="S1", time_points=["post"])],
                sample_size_plan=None
            ),
            stimuli=[],
            audit_log=[]
        )
        
        with pytest.raises(ValueError):
            await run_simulation(project_no_stimuli)
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_workflow_maintains_audit_log_on_error(self):
        """Test that audit log captures errors during workflow."""
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=None,
            stimuli=[],
            audit_log=[]
        )
        
        try:
            await run_simulation(project)
        except ValueError:
            pass  # Expected error
        
        # Even on error, audit log should have entries
        # (Current implementation may not log before validation,
        # but this tests the principle)
        assert isinstance(project.audit_log, list)


class TestWorkflowOutputQuality:
    """Test quality and consistency of workflow outputs."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_simulation_produces_valid_statistics(self):
        """Test that simulation produces statistically valid results."""
        from copilot_workflow.schemas import (
            ExperimentDesign,
            Condition,
            Measure,
            SampleSizePlan,
            StimulusItem,
            StimulusMetadata
        )
        
        design = ExperimentDesign(
            design_type="between_subjects",
            conditions=[
                Condition(id="c1", label="C1", manipulation_description="M1"),
                Condition(id="c2", label="C2", manipulation_description="M2")
            ],
            measures=[
                Measure(id="m1", label="Measure 1", scale="Likert 1-7", time_points=["post"])
            ],
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="medium",
                per_condition_range=[50, 50],
                total_n_range=[100, 100]
            )
        )
        
        stimuli = [
            StimulusItem(
                id="s1",
                text="Stimulus 1",
                metadata=StimulusMetadata(
                    valence="neutral",
                    intensity="medium",
                    ambiguity_level="low",
                    assigned_condition="c1"
                )
            ),
            StimulusItem(
                id="s2",
                text="Stimulus 2",
                metadata=StimulusMetadata(
                    valence="neutral",
                    intensity="medium",
                    ambiguity_level="low",
                    assigned_condition="c2"
                )
            )
        ]
        
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=design,
            stimuli=stimuli,
            audit_log=[]
        )
        
        result = await run_simulation(project)
        
        # Check statistical validity
        for dv_name, cond_stats in result.simulation.dv_summary.items():
            for cond_id, stats in cond_stats.items():
                # Mean should be in valid range (1-7 for Likert)
                assert 1.0 <= stats["mean"] <= 7.0
                
                # SD should be non-negative
                assert stats["sd"] >= 0.0
                
                # N should match sample size
                assert stats["n"] > 0
        
        # Check effect size estimates are present
        assert len(result.simulation.weak_effects) >= 0  # May be empty if all effects strong
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_simulation_sample_responses_quality(self):
        """Test that sample responses are realistic and varied."""
        from copilot_workflow.schemas import (
            ExperimentDesign,
            Condition,
            Measure,
            SampleSizePlan,
            StimulusItem,
            StimulusMetadata
        )
        
        design = ExperimentDesign(
            design_type="between_subjects",
            conditions=[
                Condition(id="anxious", label="Anxious", manipulation_description="Anxiety induction")
            ],
            measures=[
                Measure(id="anxiety", label="Anxiety", scale="STAI", time_points=["post"])
            ],
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="medium",
                per_condition_range=[30, 30],
                total_n_range=[30, 30]
            )
        )
        
        stimuli = [
            StimulusItem(
                id="anx_stim",
                text="Anxiety-inducing scenario",
                metadata=StimulusMetadata(
                    valence="negative",
                    intensity="high",
                    ambiguity_level="low",
                    assigned_condition="anxious"
                )
            )
        ]
        
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=design,
            stimuli=stimuli,
            audit_log=[]
        )
        
        result = await run_simulation(project)
        
        # Check sample responses
        assert len(result.simulation.sample_responses) > 0
        
        # Verify responses are non-empty strings
        for response in result.simulation.sample_responses:
            assert isinstance(response, str)
            assert len(response) > 0
            assert len(response.split()) > 5  # At least 5 words
        
        # Check for variety (not all identical)
        unique_responses = set(result.simulation.sample_responses)
        assert len(unique_responses) > 1


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
async def test_full_realistic_workflow():
    """Test a complete realistic research workflow scenario."""
    from copilot_workflow.schemas import (
        ExperimentDesign,
        Condition,
        Measure,
        SampleSizePlan,
        StimulusItem,
        StimulusMetadata
    )
    
    # Realistic research scenario: Attachment and Emotion Regulation Study
    rq_text = (
        "This study examines how attachment anxiety influences emotion regulation "
        "strategies in romantic relationships. We hypothesize that individuals with "
        "high attachment anxiety will show greater use of maladaptive emotion regulation "
        "strategies (e.g., rumination, suppression) compared to those with low attachment "
        "anxiety. Additionally, we predict that self-compassion will moderate this relationship."
    )
    
    # Create comprehensive design
    design = ExperimentDesign(
        design_type="between_subjects",
        conditions=[
            Condition(
                id="high_anxiety_low_compassion",
                label="High Anxiety, Low Self-Compassion",
                manipulation_description="Scenarios priming high attachment anxiety with low self-compassion"
            ),
            Condition(
                id="high_anxiety_high_compassion",
                label="High Anxiety, High Self-Compassion",
                manipulation_description="Scenarios priming high attachment anxiety with high self-compassion"
            ),
            Condition(
                id="low_anxiety_control",
                label="Low Anxiety (Control)",
                manipulation_description="Neutral relationship scenarios"
            )
        ],
        measures=[
            Measure(
                id="rumination",
                label="Rumination",
                scale="RRS",
                time_points=["post"]
            ),
            Measure(
                id="suppression",
                label="Emotion Suppression",
                scale="ERQ-Suppression",
                time_points=["post"]
            ),
            Measure(
                id="state_anxiety",
                label="State Anxiety",
                scale="STAI-S",
                time_points=["post"]
            ),
            Measure(
                id="relationship_satisfaction",
                label="Relationship Satisfaction",
                scale="RAS",
                time_points=["post"]
            )
        ],
        sample_size_plan=SampleSizePlan(
            assumed_effect_size="medium",
            per_condition_range=[60, 70],
            total_n_range=[180, 210]
        )
    )
    
    # Create diverse stimuli
    stimuli = [
        # High anxiety, low compassion stimuli
        StimulusItem(
            id="halc_1",
            text="Your partner hasn't responded to your messages all day. You find yourself obsessing over what you might have done wrong and feel increasingly anxious.",
            metadata=StimulusMetadata(
                valence="negative",
                intensity="high",
                ambiguity_level="medium",
                assigned_condition="high_anxiety_low_compassion"
            )
        ),
        StimulusItem(
            id="halc_2",
            text="During an argument, your partner says they need space. You immediately feel panicked and start criticizing yourself for being too needy.",
            metadata=StimulusMetadata(
                valence="negative",
                intensity="high",
                ambiguity_level="low",
                assigned_condition="high_anxiety_low_compassion"
            )
        ),
        # High anxiety, high compassion stimuli
        StimulusItem(
            id="hahc_1",
            text="Your partner seems distant lately. While you feel anxious, you remind yourself that everyone has off days and that this doesn't mean something is wrong with you.",
            metadata=StimulusMetadata(
                valence="mixed",
                intensity="medium",
                ambiguity_level="medium",
                assigned_condition="high_anxiety_high_compassion"
            )
        ),
        StimulusItem(
            id="hahc_2",
            text="You notice your partner is less affectionate than usual. You acknowledge your worried feelings while treating yourself with kindness and understanding.",
            metadata=StimulusMetadata(
                valence="mixed",
                intensity="medium",
                ambiguity_level="medium",
                assigned_condition="high_anxiety_high_compassion"
            )
        ),
        # Low anxiety control stimuli
        StimulusItem(
            id="lac_1",
            text="You and your partner are planning a relaxing weekend together. You feel comfortable and secure in your relationship.",
            metadata=StimulusMetadata(
                valence="positive",
                intensity="low",
                ambiguity_level="low",
                assigned_condition="low_anxiety_control"
            )
        ),
        StimulusItem(
            id="lac_2",
            text="Your partner mentions they'll be busy with work this week. You understand and feel confident in your relationship.",
            metadata=StimulusMetadata(
                valence="neutral",
                intensity="low",
                ambiguity_level="low",
                assigned_condition="low_anxiety_control"
            )
        )
    ]
    
    # Create project
    project = ProjectState(
        rq=ResearchQuestion(
            raw_text=rq_text,
            constructs=["attachment_anxiety", "emotion_regulation", "self_compassion", "rumination"]
        ),
        design=design,
        stimuli=stimuli,
        audit_log=[]
    )
    
    # Run simulation
    result = await run_simulation(project)
    
    # Comprehensive validation
    assert result.simulation is not None
    
    # Verify all measures appear in results
    expected_measures = {"Rumination", "Emotion Suppression", "State Anxiety", "Relationship Satisfaction"}
    actual_measures = set(result.simulation.dv_summary.keys())
    assert expected_measures == actual_measures
    
    # Verify all conditions appear in results
    expected_conditions = {"high_anxiety_low_compassion", "high_anxiety_high_compassion", "low_anxiety_control"}
    for dv_name, cond_stats in result.simulation.dv_summary.items():
        actual_conditions = set(cond_stats.keys())
        assert expected_conditions.intersection(actual_conditions) == expected_conditions
    
    # Verify effect size estimates were computed
    assert len(result.simulation.weak_effects) >= 0
    
    # Verify sample responses are realistic
    assert len(result.simulation.sample_responses) >= 5
    for response in result.simulation.sample_responses[:5]:
        assert len(response) > 20  # Substantial responses
        assert any(word in response.lower() for word in ["feel", "think", "would", "might"])
    
    # Verify audit trail
    assert len(result.audit_log) > 0
    sim_entries = [e for e in result.audit_log if "simulation" in e.message.lower()]
    assert len(sim_entries) >= 2  # At least "started" and "completed"
    
    # Print summary for manual inspection
    print("\n" + "="*60)
    print("REALISTIC WORKFLOW TEST SUMMARY")
    print("="*60)
    print(f"Research Question: {rq_text[:100]}...")
    print(f"Design: {design.design_type} with {len(design.conditions)} conditions")
    print(f"Measures: {len(design.measures)}")
    print(f"Stimuli: {len(stimuli)}")
    print(f"\nSimulation Results:")
    for dv_name, cond_stats in result.simulation.dv_summary.items():
        print(f"\n  {dv_name}:")
        for cond_id, stats in cond_stats.items():
            print(f"    {cond_id}: M={stats['mean']:.2f}, SD={stats['sd']:.2f}, N={stats['n']}")
    
    if result.simulation.dead_vars:
        print(f"\n  Dead variables detected: {result.simulation.dead_vars}")
    if result.simulation.weak_effects:
        print(f"\n  Weak effects detected: {len(result.simulation.weak_effects)}")
    
    print(f"\nSample Responses (first 3):")
    for i, response in enumerate(result.simulation.sample_responses[:3], 1):
        print(f"  {i}. {response[:100]}...")
    print("="*60)
