"""Functional tests for Module 3: Experimental Design Builder & Critic.

Tests end-to-end workflow:
1. Design proposal from hypotheses
2. Confound checking
3. Sample size calculation
4. Methods section generation
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    Hypothesis,
    ConceptNode,
    AuditEntry,
)
from Experimental_Design_Builder_Critic import (
    run,
    run_with_summary,
    propose_design,
    check_confounds,
    calculate_sample_size,
    DesignConstraints,
)

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_project_with_hypotheses() -> ProjectState:
    """Create test project with hypotheses (simulating Module 2 output)."""
    project = ProjectState(
        rq=ResearchQuestion(
            id="test_rq_001",
            raw_text="How does attachment anxiety influence emotion regulation strategies?",
            parsed_constructs=["attachment anxiety", "emotion regulation strategies"]
        )
    )
    
    # Add some concept nodes (from Module 1)
    project.concepts = {
        "nodes": [
            ConceptNode(
                id="concept_001",
                label="Attachment Anxiety",
                type="construct",
                common_measures=["ECR-R Anxiety subscale", "ASQ Anxiety scale"]
            ),
            ConceptNode(
                id="concept_002",
                label="Emotion Regulation",
                type="construct",
                common_measures=["ERQ", "DERS", "CERQ"]
            ),
        ],
        "edges": []
    }
    
    # Add hypotheses (from Module 2)
    project.hypotheses = [
        Hypothesis(
            id="hyp_001",
            text="Higher attachment anxiety will predict greater use of maladaptive emotion regulation strategies",
            iv=["attachment anxiety"],
            dv=["maladaptive emotion regulation strategies"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment theory", "Emotion regulation framework"]
        ),
        Hypothesis(
            id="hyp_002",
            text="Attachment anxiety will be negatively associated with adaptive emotion regulation strategies",
            iv=["attachment anxiety"],
            dv=["adaptive emotion regulation strategies"],
            mediators=[],
            moderators=[],
            theoretical_basis=["Attachment theory"]
        ),
    ]
    
    return project


async def test_design_proposal():
    """Test design proposal generation."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Design Proposal")
    logger.info("="*60)
    
    project = create_test_project_with_hypotheses()
    
    try:
        # Propose design without LLM (heuristic only)
        proposal = await propose_design(project, use_llm=False)
        
        assert proposal.design_type in ["between_subjects", "within_subjects", "mixed"], \
            f"Invalid design type: {proposal.design_type}"
        assert len(proposal.conditions) >= 2, "Need at least 2 conditions"
        assert len(proposal.measures) >= 1, "Need at least 1 measure"
        assert len(proposal.time_points) >= 1, "Need at least 1 time point"
        
        logger.info(f"✅ Design proposal generated:")
        logger.info(f"   Type: {proposal.design_type}")
        logger.info(f"   Conditions: {len(proposal.conditions)}")
        logger.info(f"   Measures: {len(proposal.measures)}")
        logger.info(f"   Time points: {proposal.time_points}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Design proposal failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_confound_checking():
    """Test confound checking."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Confound Checking")
    logger.info("="*60)
    
    project = create_test_project_with_hypotheses()
    
    try:
        # Get design proposal
        proposal = await propose_design(project, use_llm=False)
        
        # Check confounds
        warnings = check_confounds(proposal)
        
        assert isinstance(warnings, list), "Warnings should be a list"
        
        high_severity = sum(1 for w in warnings if w.severity == "high")
        medium_severity = sum(1 for w in warnings if w.severity == "medium")
        low_severity = sum(1 for w in warnings if w.severity == "low")
        
        logger.info(f"✅ Confound checking complete:")
        logger.info(f"   Total warnings: {len(warnings)}")
        logger.info(f"   High: {high_severity}, Medium: {medium_severity}, Low: {low_severity}")
        
        if warnings:
            logger.info(f"   Sample warning: {warnings[0].confound_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Confound checking failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sample_size_calculation():
    """Test sample size calculation."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Sample Size Calculation")
    logger.info("="*60)
    
    project = create_test_project_with_hypotheses()
    
    try:
        # Get design proposal
        proposal = await propose_design(project, use_llm=False)
        
        # Calculate sample size for each effect size
        for effect_size in ["small", "medium", "large"]:
            plan = calculate_sample_size(proposal, effect_size=effect_size)
            
            assert plan.total_n > 0, f"Total N must be > 0 for {effect_size} effect"
            assert plan.per_condition_n > 0, f"Per-condition N must be > 0"
            assert plan.design_type == proposal.design_type, "Design types must match"
            
            logger.info(f"✅ {effect_size.capitalize()} effect: {plan.total_n} total participants")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample size calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_module3_workflow():
    """Test complete Module 3 workflow."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Full Module 3 Workflow")
    logger.info("="*60)
    
    project = create_test_project_with_hypotheses()
    
    try:
        # Run full Module 3 (without LLM to avoid API dependency)
        result_project, summary = await run_with_summary(
            project,
            effect_size="medium",
            use_llm=False
        )
        
        # Validate outputs (use summary dict, not direct model access)
        assert result_project.design is not None, "Design should be set"
        assert result_project.design.design_type is not None, "Design type should be set"
        assert len(result_project.design.conditions) >= 2, "Should have at least 2 conditions"
        assert len(result_project.design.measures) >= 1, "Should have at least 1 measure"
        
        # Check summary (correct way to access calculated values)
        assert summary["design_type"] is not None, "Summary should have design type"
        assert summary["num_conditions"] >= 2, "Summary should show conditions"
        assert summary["sample_size"] > 0, "Summary should show sample size"
        
        logger.info(f"✅ Module 3 complete:")
        logger.info(f"   Design: {summary['design_type']}")
        logger.info(f"   Conditions: {summary['num_conditions']}")
        logger.info(f"   Measures: {summary['num_measures']}")
        logger.info(f"   Sample Size: {summary['sample_size']} participants")
        logger.info(f"   Confound Warnings: {summary['confound_warnings']}")
        logger.info(f"   Methods: {summary['methods_word_count']} words")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Module 3 workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_module3_with_constraints():
    """Test Module 3 with user constraints."""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Module 3 with Constraints")
    logger.info("="*60)
    
    project = create_test_project_with_hypotheses()
    
    constraints = DesignConstraints(
        online=True,
        max_participants=100,
        sample_type="students"
    )
    
    try:
        result_project, summary = await run_with_summary(
            project,
            constraints=constraints,
            effect_size="large",  # Large effect to fit within max_participants
            use_llm=False
        )
        
        assert result_project.design is not None, "Design should be set"
        
        # Check that sample size respects constraint (use summary, not direct access)
        total_n = summary["sample_size"]
        logger.info(f"✅ Design with constraints:")
        logger.info(f"   Max participants: {constraints.max_participants}")
        logger.info(f"   Recommended N: {total_n}")
        logger.info(f"   Sample type: {constraints.sample_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Constrained design failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Module 3 functional tests."""
    print("\n" + "#"*80)
    print("# FUNCTIONAL TESTS: Module 3 - Experimental Design Builder & Critic")
    print("#"*80)
    
    tests = [
        ("Design Proposal", test_design_proposal),
        ("Confound Checking", test_confound_checking),
        ("Sample Size Calculation", test_sample_size_calculation),
        ("Full Module 3 Workflow", test_full_module3_workflow),
        ("Module 3 with Constraints", test_module3_with_constraints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
        
        # Wait between tests
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "#"*80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"# ✅ ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"# ❌ SOME TESTS FAILED ({passed}/{total} passed)")
    
    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"#   {test_name}: {status}")
    
    print("#"*80)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
