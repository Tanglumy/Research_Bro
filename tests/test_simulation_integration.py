"""Integration tests for Synthetic Participant Simulator module.

Tests the integration of all simulation components:
- Persona modeling
- Response simulation
- Diagnostics engine
- Complete simulation workflow
"""

import pytest
import asyncio
from typing import List

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    ExperimentDesign,
    Condition,
    Measure,
    SampleSizePlan,
    StimulusItem,
    StimulusMetadata,
    Persona,
    SyntheticParticipant,
    AuditEntry
)

from Synthetic_Participant_Simulator import (
    PersonaGenerator,
    ResponseSimulator,
    DiagnosticsEngine,
    SyntheticParticipantSimulator
)


@pytest.fixture
def sample_design():
    """Create a sample experimental design for testing."""
    return ExperimentDesign(
        design_type="between_subjects",
        conditions=[
            Condition(
                id="negative_high",
                label="Negative High Intensity",
                manipulation_description="High intensity negative scenario"
            ),
            Condition(
                id="negative_low",
                label="Negative Low Intensity",
                manipulation_description="Low intensity negative scenario"
            ),
            Condition(
                id="positive",
                label="Positive Control",
                manipulation_description="Positive scenario"
            )
        ],
        measures=[
            Measure(
                id="anxiety",
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
            per_condition_range=[40, 60],
            total_n_range=[120, 180]
        )
    )


@pytest.fixture
def sample_stimuli():
    """Create sample stimuli for testing."""
    return [
        StimulusItem(
            id="stim_001",
            text="Your partner criticizes you harshly in front of friends.",
            metadata=StimulusMetadata(
                valence="negative",
                intensity="high",
                ambiguity_level="low",
                assigned_condition="negative_high"
            )
        ),
        StimulusItem(
            id="stim_002",
            text="Your partner makes a minor critical comment.",
            metadata=StimulusMetadata(
                valence="negative",
                intensity="low",
                ambiguity_level="low",
                assigned_condition="negative_low"
            )
        ),
        StimulusItem(
            id="stim_003",
            text="Your partner expresses appreciation and support.",
            metadata=StimulusMetadata(
                valence="positive",
                intensity="medium",
                ambiguity_level="low",
                assigned_condition="positive"
            )
        ),
        StimulusItem(
            id="stim_004",
            text="You receive harsh feedback from a colleague at work.",
            metadata=StimulusMetadata(
                valence="negative",
                intensity="high",
                ambiguity_level="low",
                assigned_condition="negative_high"
            )
        ),
        StimulusItem(
            id="stim_005",
            text="A friend gently points out a mistake you made.",
            metadata=StimulusMetadata(
                valence="negative",
                intensity="low",
                ambiguity_level="low",
                assigned_condition="negative_low"
            )
        ),
        StimulusItem(
            id="stim_006",
            text="You receive praise and recognition from your team.",
            metadata=StimulusMetadata(
                valence="positive",
                intensity="medium",
                ambiguity_level="low",
                assigned_condition="positive"
            )
        )
    ]


class TestPersonaGeneration:
    """Test persona generation integration."""
    
    def test_persona_generator_creates_diverse_profiles(self, sample_design):
        """Test that persona generator creates diverse profiles."""
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=100, design=sample_design)
        
        # Check count
        assert len(personas) == 100
        
        # Check diversity of attachment styles
        attachment_styles = [p.attachment_style for p in personas]
        unique_styles = set(attachment_styles)
        assert len(unique_styles) >= 3  # At least 3 different styles
        
        # Check all have personality traits
        for persona in personas:
            assert "neuroticism" in persona.personality_traits
            assert "extraversion" in persona.personality_traits
            assert 0 <= persona.personality_traits["neuroticism"] <= 100
            assert 0 <= persona.personality_traits["extraversion"] <= 100
    
    def test_persona_trait_correlations(self, sample_design):
        """Test that persona traits show expected correlations."""
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=100, design=sample_design)
        
        # Anxious attachment should correlate with higher neuroticism
        anxious_personas = [p for p in personas if p.attachment_style == "anxious"]
        if len(anxious_personas) > 0:
            avg_neuroticism = sum(p.personality_traits["neuroticism"] for p in anxious_personas) / len(anxious_personas)
            assert avg_neuroticism > 55  # Should be above average
        
        # Secure attachment should correlate with lower neuroticism
        secure_personas = [p for p in personas if p.attachment_style == "secure"]
        if len(secure_personas) > 0:
            avg_neuroticism = sum(p.personality_traits["neuroticism"] for p in secure_personas) / len(secure_personas)
            assert avg_neuroticism < 55  # Should be below average


class TestResponseSimulation:
    """Test response simulation integration."""
    
    @pytest.mark.asyncio
    async def test_response_simulator_generates_scores(self, sample_design, sample_stimuli):
        """Test that response simulator generates DV scores."""
        simulator = ResponseSimulator()
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=10, design=sample_design)
        
        # Simulate responses for first persona and first stimulus
        persona = personas[0]
        stimulus = sample_stimuli[0]
        
        response = await simulator.simulate_response(persona, stimulus, sample_design)
        
        # Check response structure
        assert response.stimulus_id == stimulus.id
        assert response.condition_id == stimulus.metadata.assigned_condition
        assert "State Anxiety" in response.dv_scores
        assert "Self-Compassion" in response.dv_scores
        
        # Check score ranges (1-7 Likert scale)
        for dv_name, score in response.dv_scores.items():
            assert 1.0 <= score <= 7.0
    
    @pytest.mark.asyncio
    async def test_response_varies_by_attachment_style(self, sample_design, sample_stimuli):
        """Test that responses vary appropriately by attachment style."""
        simulator = ResponseSimulator()
        
        # Create personas with specific attachment styles
        anxious_persona = Persona(
            attachment_style="anxious",
            self_criticism="high",
            culture="individualistic",
            personality_traits={"neuroticism": 70, "extraversion": 50, "openness": 50, "agreeableness": 50, "conscientiousness": 50},
            demographic_info={"age": 25, "gender": "female"},
            other_traits={}
        )
        
        secure_persona = Persona(
            attachment_style="secure",
            self_criticism="low",
            culture="individualistic",
            personality_traits={"neuroticism": 30, "extraversion": 50, "openness": 50, "agreeableness": 60, "conscientiousness": 50},
            demographic_info={"age": 25, "gender": "female"},
            other_traits={}
        )
        
        # Use negative high intensity stimulus
        negative_stimulus = sample_stimuli[0]
        
        # Simulate responses
        anxious_response = await simulator.simulate_response(anxious_persona, negative_stimulus, sample_design)
        secure_response = await simulator.simulate_response(secure_persona, negative_stimulus, sample_design)
        
        # Anxious should have higher anxiety scores on negative stimuli
        assert anxious_response.dv_scores["State Anxiety"] > secure_response.dv_scores["State Anxiety"]
    
    @pytest.mark.asyncio
    async def test_response_generates_open_text(self, sample_design, sample_stimuli):
        """Test that open text responses are generated."""
        simulator = ResponseSimulator()
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=5, design=sample_design)
        
        for persona in personas:
            response = await simulator.simulate_response(persona, sample_stimuli[0], sample_design)
            assert response.open_text is not None
            assert len(response.open_text) > 0
            assert isinstance(response.open_text, str)


class TestDiagnosticsEngine:
    """Test diagnostics engine integration."""
    
    @pytest.mark.asyncio
    async def test_diagnostics_computes_condition_means(self, sample_design, sample_stimuli):
        """Test that diagnostics engine computes condition means correctly."""
        # Create participants with responses
        simulator_obj = SyntheticParticipantSimulator()
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=30, design=sample_design)
        
        participants = []
        for persona in personas:
            participant = await simulator_obj._simulate_participant(persona, sample_design, sample_stimuli)
            participants.append(participant)
        
        # Compute diagnostics
        diagnostics_engine = DiagnosticsEngine()
        results = diagnostics_engine.compute_diagnostics(participants, sample_design)
        
        # Check structure
        assert "condition_means" in results
        assert "dead_variables" in results
        assert "weak_effects" in results
        assert "effect_estimates" in results
        
        # Check condition means
        assert "State Anxiety" in results["condition_means"]
        condition_stats = results["condition_means"]["State Anxiety"]
        
        # Should have stats for each condition
        for condition in sample_design.conditions:
            assert condition.id in condition_stats
            assert "mean" in condition_stats[condition.id]
            assert "sd" in condition_stats[condition.id]
            assert "n" in condition_stats[condition.id]
    
    @pytest.mark.asyncio
    async def test_diagnostics_detects_dead_variables(self, sample_design):
        """Test that diagnostics can detect dead variables."""
        # Create participants with constant responses (dead variable)
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=20, design=sample_design)
        
        # Create synthetic participants with fixed responses
        from copilot_workflow.schemas import SyntheticResponse
        participants = []
        for persona in personas:
            responses = [
                SyntheticResponse(
                    stimulus_id="stim_001",
                    condition_id="negative_high",
                    dv_scores={"State Anxiety": 4.0, "Self-Compassion": 4.0},  # Constant scores
                    open_text="Response"
                )
            ]
            participants.append(SyntheticParticipant(persona=persona, responses=responses))
        
        # Compute diagnostics
        diagnostics_engine = DiagnosticsEngine()
        results = diagnostics_engine.compute_diagnostics(participants, sample_design)
        
        # Both variables should be detected as dead (SD = 0)
        assert len(results["dead_variables"]) > 0
    
    @pytest.mark.asyncio
    async def test_diagnostics_computes_effect_sizes(self, sample_design, sample_stimuli):
        """Test that diagnostics computes effect sizes correctly."""
        # Create participants
        simulator_obj = SyntheticParticipantSimulator()
        generator = PersonaGenerator()
        personas = generator.create_personas(n_participants=60, design=sample_design)
        
        participants = []
        for persona in personas:
            participant = await simulator_obj._simulate_participant(persona, sample_design, sample_stimuli)
            participants.append(participant)
        
        # Compute diagnostics
        diagnostics_engine = DiagnosticsEngine()
        results = diagnostics_engine.compute_diagnostics(participants, sample_design)
        
        # Check effect size estimates
        assert len(results["effect_estimates"]) > 0
        
        for effect in results["effect_estimates"]:
            assert "dv" in effect
            assert "condition1" in effect
            assert "condition2" in effect
            assert "cohens_d" in effect
            assert "interpretation" in effect
            assert effect["interpretation"] in ["negligible", "small", "medium", "large"]


class TestCompleteSimulation:
    """Test complete simulation workflow integration."""
    
    @pytest.mark.asyncio
    async def test_full_simulation_workflow(self, sample_design, sample_stimuli):
        """Test the complete simulation workflow from start to finish."""
        # Create project state
        project = ProjectState(
            rq=ResearchQuestion(
                raw_text="Test research question",
                constructs=["attachment", "emotion_regulation"]
            ),
            design=sample_design,
            stimuli=sample_stimuli,
            audit_log=[]
        )
        
        # Run simulation
        from Synthetic_Participant_Simulator import run
        result_project = await run(project)
        
        # Check simulation was added to project
        assert result_project.simulation is not None
        
        # Check simulation summary structure
        assert result_project.simulation.dv_summary is not None
        assert result_project.simulation.dead_vars is not None
        assert result_project.simulation.weak_effects is not None
        assert result_project.simulation.sample_responses is not None
        
        # Check audit log was updated
        assert len(result_project.audit_log) > 0
        simulation_entries = [e for e in result_project.audit_log if "simulation" in e.message.lower()]
        assert len(simulation_entries) > 0
    
    @pytest.mark.asyncio
    async def test_simulation_with_different_sample_sizes(self, sample_design, sample_stimuli):
        """Test simulation with different sample sizes."""
        simulator = SyntheticParticipantSimulator()
        
        for n in [10, 50, 100]:
            # Adjust sample size plan
            design = ExperimentDesign(
                design_type=sample_design.design_type,
                conditions=sample_design.conditions,
                measures=sample_design.measures,
                sample_size_plan=SampleSizePlan(
                    assumed_effect_size="medium",
                    per_condition_range=[n // 3, n // 3],
                    total_n_range=[n, n]
                )
            )
            
            project = ProjectState(
                rq=ResearchQuestion(raw_text="Test", constructs=[]),
                design=design,
                stimuli=sample_stimuli,
                audit_log=[]
            )
            
            result = await simulator.run(project)
            
            # Check appropriate number of responses generated
            total_responses = sum(
                stats["n"] 
                for dv_stats in result.simulation.dv_summary.values()
                for stats in dv_stats.values()
            )
            assert total_responses >= n  # Should have at least n responses
    
    @pytest.mark.asyncio
    async def test_simulation_error_handling(self):
        """Test simulation error handling with invalid inputs."""
        simulator = SyntheticParticipantSimulator()
        
        # Test with missing design
        project_no_design = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=None,
            stimuli=[],
            audit_log=[]
        )
        
        with pytest.raises(ValueError, match="No experimental design found"):
            await simulator.run(project_no_design)
        
        # Test with missing stimuli
        project_no_stimuli = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=ExperimentDesign(
                design_type="between_subjects",
                conditions=[],
                measures=[],
                sample_size_plan=None
            ),
            stimuli=[],
            audit_log=[]
        )
        
        with pytest.raises(ValueError, match="No stimuli found"):
            await simulator.run(project_no_stimuli)


class TestCrossModuleIntegration:
    """Test integration with other workflow modules."""
    
    @pytest.mark.asyncio
    async def test_simulation_uses_design_conditions(self, sample_design, sample_stimuli):
        """Test that simulation correctly uses design conditions."""
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=sample_design,
            stimuli=sample_stimuli,
            audit_log=[]
        )
        
        from Synthetic_Participant_Simulator import run
        result = await run(project)
        
        # Check that all conditions appear in results
        condition_ids = {c.id for c in sample_design.conditions}
        
        for dv_name, cond_stats in result.simulation.dv_summary.items():
            result_condition_ids = set(cond_stats.keys())
            # All design conditions should appear in at least one DV
            assert len(result_condition_ids.intersection(condition_ids)) > 0
    
    @pytest.mark.asyncio
    async def test_simulation_uses_stimulus_metadata(self, sample_design, sample_stimuli):
        """Test that simulation uses stimulus metadata correctly."""
        simulator = SyntheticParticipantSimulator()
        generator = PersonaGenerator()
        response_sim = ResponseSimulator()
        
        # Create a high neuroticism persona
        persona = Persona(
            attachment_style="anxious",
            self_criticism="high",
            culture="individualistic",
            personality_traits={"neuroticism": 80, "extraversion": 50, "openness": 50, "agreeableness": 50, "conscientiousness": 50},
            demographic_info={"age": 25, "gender": "female"},
            other_traits={}
        )
        
        # Test with different valences
        negative_stimulus = [s for s in sample_stimuli if s.metadata.valence == "negative"][0]
        positive_stimulus = [s for s in sample_stimuli if s.metadata.valence == "positive"][0]
        
        neg_response = await response_sim.simulate_response(persona, negative_stimulus, sample_design)
        pos_response = await response_sim.simulate_response(persona, positive_stimulus, sample_design)
        
        # Negative stimulus should produce higher anxiety than positive
        assert neg_response.dv_scores["State Anxiety"] > pos_response.dv_scores["State Anxiety"]


# Performance and stress tests
class TestSimulationPerformance:
    """Test simulation performance and scalability."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_scale_simulation(self, sample_design, sample_stimuli):
        """Test simulation with large number of participants."""
        import time
        
        # Modify design for larger sample
        large_design = ExperimentDesign(
            design_type=sample_design.design_type,
            conditions=sample_design.conditions,
            measures=sample_design.measures,
            sample_size_plan=SampleSizePlan(
                assumed_effect_size="small",
                per_condition_range=[100, 100],
                total_n_range=[300, 300]
            )
        )
        
        project = ProjectState(
            rq=ResearchQuestion(raw_text="Test", constructs=[]),
            design=large_design,
            stimuli=sample_stimuli * 10,  # More stimuli
            audit_log=[]
        )
        
        start_time = time.time()
        from Synthetic_Participant_Simulator import run
        result = await run(project)
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed_time < 30
        
        # Check results were generated
        assert result.simulation is not None
        assert len(result.simulation.dv_summary) > 0
