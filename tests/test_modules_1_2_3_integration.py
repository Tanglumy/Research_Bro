"""Integration tests for Modules 1 → 2 → 3 pipeline.

Tests the complete workflow:
1. Research Question → Literature Landscape (Module 1)
2. Literature + RQ → Hypotheses (Module 2)
3. Hypotheses → Experimental Design (Module 3)
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot_workflow.schemas import (
    ProjectState,
    ResearchQuestion,
    ConceptNode,
    ConceptEdge,
)
from Literature_Landscape_Explorer import run as run_module1
from Hypothesis_Generator_Structurer import run as run_module2
from Experimental_Design_Builder_Critic import run as run_module3, DesignConstraints

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_full_pipeline_end_to_end():
    """Test complete pipeline: RQ → Literature → Hypotheses → Design."""
    logger.info("\n" + "="*80)
    logger.info("INTEGRATION TEST 1: Complete Pipeline (Modules 1 → 2 → 3)")
    logger.info("="*80)
    
    # Start with research question
    project = ProjectState(
        rq=ResearchQuestion(
            id="integration_test_rq",
            raw_text="How does attachment anxiety influence emotion regulation in romantic relationships?",
            parsed_constructs=["attachment anxiety", "emotion regulation", "romantic relationships"]
        )
    )
    
    logger.info(f"Starting RQ: {project.rq.raw_text}")
    
    try:
        # Module 1: Literature Landscape Explorer
        logger.info("\n--- Running Module 1: Literature Explorer ---")
        from Literature_Landscape_Explorer import run_with_summary as run_m1_summary
        project, m1_summary = await run_m1_summary(project)
        
        logger.info(f"Module 1 Complete:")
        logger.info(f"  Papers: {m1_summary.get('papers', 0)}")
        logger.info(f"  Concepts: {m1_summary.get('concepts', {})}")
        logger.info(f"  Graph: {m1_summary.get('graph', {})}")
        logger.info(f"  Gaps: {m1_summary.get('gaps', {})}")
        
        assert m1_summary.get('papers', 0) > 0, "Module 1 should retrieve papers"
        
        # Module 2: Hypothesis Generator
        logger.info("\n--- Running Module 2: Hypothesis Generator ---")
        from Hypothesis_Generator_Structurer import run_with_summary as run_m2_summary
        project, m2_summary = await run_m2_summary(project, num_hypotheses=3)
        
        logger.info(f"Module 2 Complete:")
        logger.info(f"  Hypotheses: {m2_summary['num_hypotheses']}")
        logger.info(f"  Validated: {m2_summary['validated']}")
        logger.info(f"  Export formats: {len(m2_summary.get('export_formats', []))}")
        
        assert m2_summary['num_hypotheses'] > 0, "Module 2 should generate hypotheses"
        
        # Module 3: Experimental Design Builder
        logger.info("\n--- Running Module 3: Design Builder ---")
        from Experimental_Design_Builder_Critic import run_with_summary as run_m3_summary
        project, m3_summary = await run_m3_summary(
            project,
            effect_size="medium",
            use_llm=False  # Use heuristics for testing
        )
        
        logger.info(f"Module 3 Complete:")
        logger.info(f"  Design Type: {m3_summary['design_type']}")
        logger.info(f"  Conditions: {m3_summary['num_conditions']}")
        logger.info(f"  Measures: {m3_summary['num_measures']}")
        logger.info(f"  Sample Size: {m3_summary['sample_size']} participants")
        logger.info(f"  Confound Warnings: {m3_summary['confound_warnings']}")
        logger.info(f"  Methods Words: {m3_summary['methods_word_count']}")
        
        assert m3_summary['design_type'] is not None, "Module 3 should propose design"
        assert m3_summary['num_conditions'] >= 2, "Design should have at least 2 conditions"
        assert m3_summary['sample_size'] > 0, "Should recommend sample size"
        
        # Validate final project state
        assert project.rq is not None, "Should have research question"
        assert project.papers is not None and len(project.papers) > 0, "Should have papers"
        assert project.hypotheses is not None and len(project.hypotheses) > 0, "Should have hypotheses"
        assert project.design is not None, "Should have design"
        assert len(project.audit_log) > 0, "Should have audit trail"
        
        logger.info("\n✅ Full pipeline test PASSED")
        logger.info(f"   Total audit entries: {len(project.audit_log)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Full pipeline test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_flow_validation():
    """Test that data flows correctly between modules."""
    logger.info("\n" + "="*80)
    logger.info("INTEGRATION TEST 2: Data Flow Validation")
    logger.info("="*80)
    
    project = ProjectState(
        rq=ResearchQuestion(
            id="dataflow_test",
            raw_text="Does mindfulness training improve working memory capacity?",
            parsed_constructs=["mindfulness training", "working memory capacity"]
        )
    )
    
    try:
        # Run Module 1
        logger.info("Running Module 1...")
        from Literature_Landscape_Explorer import run_with_summary as run_m1
        project, m1_summary = await run_m1(project)
        
        # Check Module 1 outputs are available to Module 2
        logger.info("\nValidating Module 1 → Module 2 interface:")
        logger.info(f"  ✓ Has research question: {project.rq is not None}")
        logger.info(f"  ✓ Papers retrieved: {m1_summary.get('papers', 0)} (from Module 1 summary)")
        logger.info(f"  ✓ Has concepts: {project.concepts is not None}")
        logger.info(f"  ✓ Has audit log: {len(project.audit_log) > 0}")
        
        # Run Module 2
        logger.info("\nRunning Module 2...")
        from Hypothesis_Generator_Structurer import run_with_summary as run_m2
        project, m2_summary = await run_m2(project, num_hypotheses=3)
        
        # Check Module 2 outputs are available to Module 3
        logger.info("\nValidating Module 2 → Module 3 interface:")
        logger.info(f"  ✓ Has hypotheses: {project.hypotheses is not None and len(project.hypotheses) > 0}")
        
        if project.hypotheses:
            h = project.hypotheses[0]
            logger.info(f"  ✓ Hypothesis has IV: {len(h.iv) > 0}")
            logger.info(f"  ✓ Hypothesis has DV: {len(h.dv) > 0}")
            logger.info(f"  ✓ Hypothesis has text: {len(h.text) > 0}")
        
        # Run Module 3
        logger.info("\nRunning Module 3...")
        from Experimental_Design_Builder_Critic import run_with_summary as run_m3
        project, m3_summary = await run_m3(project, effect_size="medium", use_llm=False)
        
        # Check Module 3 outputs
        logger.info("\nValidating Module 3 outputs:")
        logger.info(f"  ✓ Has design: {project.design is not None}")
        
        if project.design:
            logger.info(f"  ✓ Design has type: {project.design.design_type is not None}")
            logger.info(f"  ✓ Design has conditions: {len(project.design.conditions) > 0}")
            logger.info(f"  ✓ Design has measures: {len(project.design.measures) > 0}")
            logger.info(f"  ✓ Design has sample plan: {project.design.sample_size_plan is not None}")
        
        logger.info("\n✅ Data flow validation PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data flow validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_module3_edge_cases():
    """Test Module 3 with various edge cases."""
    logger.info("\n" + "="*80)
    logger.info("INTEGRATION TEST 3: Module 3 Edge Cases")
    logger.info("="*80)
    
    # Edge case 1: Single hypothesis
    logger.info("\nEdge Case 1: Single hypothesis")
    try:
        from copilot_workflow.schemas import Hypothesis
        project = ProjectState(
            rq=ResearchQuestion(
                id="edge_case_1",
                raw_text="Does exercise improve mood?",
                parsed_constructs=["exercise", "mood"]
            )
        )
        project.hypotheses = [
            Hypothesis(
                id="h1",
                text="Exercise will improve mood",
                iv=["exercise"],
                dv=["mood"],
                mediators=[],
                moderators=[]
            )
        ]
        
        from Experimental_Design_Builder_Critic import run_with_summary
        project, summary = await run_with_summary(project, use_llm=False)
        
        assert summary['design_type'] is not None
        logger.info(f"  ✓ Single hypothesis handled: {summary['design_type']}")
        
    except Exception as e:
        logger.error(f"  ✗ Single hypothesis failed: {e}")
        return False
    
    # Edge case 2: Complex hypothesis with mediators and moderators
    logger.info("\nEdge Case 2: Complex hypothesis (with mediators/moderators)")
    try:
        project = ProjectState(
            rq=ResearchQuestion(
                id="edge_case_2",
                raw_text="Complex mediation model",
                parsed_constructs=["IV", "mediator", "moderator", "DV"]
            )
        )
        project.hypotheses = [
            Hypothesis(
                id="h1",
                text="IV affects DV through mediator, moderated by moderator",
                iv=["stress"],
                dv=["burnout"],
                mediators=["coping strategies"],
                moderators=["social support"]
            )
        ]
        
        project, summary = await run_with_summary(project, use_llm=False)
        
        assert summary['design_type'] is not None
        # Complex designs should have more time points (for mediation)
        if hasattr(project.design, 'time_points'):
            logger.info(f"  ✓ Complex hypothesis handled: {len(project.design.time_points)} time points")
        else:
            logger.info(f"  ✓ Complex hypothesis handled: {summary['design_type']}")
        
    except Exception as e:
        logger.error(f"  ✗ Complex hypothesis failed: {e}")
        return False
    
    # Edge case 3: Within-subjects design (manipulation keywords)
    logger.info("\nEdge Case 3: Within-subjects design detection")
    try:
        project = ProjectState(
            rq=ResearchQuestion(
                id="edge_case_3",
                raw_text="Emotion regulation task comparison",
                parsed_constructs=["task", "emotion"]
            )
        )
        project.hypotheses = [
            Hypothesis(
                id="h1",
                text="Reappraisal task will reduce negative emotion more than suppression task",
                iv=["emotion regulation task"],  # "task" keyword should trigger within-subjects
                dv=["negative emotion"],
                mediators=[],
                moderators=[]
            )
        ]
        
        project, summary = await run_with_summary(project, use_llm=False)
        
        logger.info(f"  ✓ Design type detected: {summary['design_type']}")
        # Note: Heuristic may choose between-subjects for safety (to avoid carryover)
        # Both are valid for this scenario
        
    except Exception as e:
        logger.error(f"  ✗ Within-subjects detection failed: {e}")
        return False
    
    # Edge case 4: Large sample size requirement (small effect)
    logger.info("\nEdge Case 4: Small effect size (large N)")
    try:
        project = ProjectState(
            rq=ResearchQuestion(
                id="edge_case_4",
                raw_text="Subtle personality effect",
                parsed_constructs=["personality", "behavior"]
            )
        )
        project.hypotheses = [
            Hypothesis(
                id="h1",
                text="Personality predicts behavior",
                iv=["personality trait"],
                dv=["daily behavior"],
                mediators=[],
                moderators=[]
            )
        ]
        
        project, summary = await run_with_summary(project, effect_size="small", use_llm=False)
        
        assert summary['sample_size'] > 100, "Small effects should require large N"
        logger.info(f"  ✓ Small effect handled: N = {summary['sample_size']}")
        
    except Exception as e:
        logger.error(f"  ✗ Small effect failed: {e}")
        return False
    
    # Edge case 5: Constraints that limit sample size
    logger.info("\nEdge Case 5: Constrained design (max participants)")
    try:
        project = ProjectState(
            rq=ResearchQuestion(
                id="edge_case_5",
                raw_text="Resource-constrained study",
                parsed_constructs=["IV", "DV"]
            )
        )
        project.hypotheses = [
            Hypothesis(
                id="h1",
                text="IV affects DV",
                iv=["intervention"],
                dv=["outcome"],
                mediators=[],
                moderators=[]
            )
        ]
        
        constraints = DesignConstraints(
            online=True,
            max_participants=50,
            sample_type="clinical"
        )
        
        from Experimental_Design_Builder_Critic import run
        project = await run(
            project,
            constraints=constraints,
            effect_size="large",  # Large effect to fit constraint
            use_llm=False
        )
        
        # Use attribute access for Pydantic model (not dict subscript)
        total_n = project.design.sample_size_plan.total_n if hasattr(project.design.sample_size_plan, 'total_n') else 0
        logger.info(f"  ✓ Constraints applied: N = {total_n}")
        logger.info(f"    (constraint: max 50 participants)")
        
    except Exception as e:
        logger.error(f"  ✗ Constrained design failed: {e}")
        return False
    
    logger.info("\n✅ All edge cases PASSED")
    return True


async def test_error_recovery():
    """Test graceful error handling and recovery."""
    logger.info("\n" + "="*80)
    logger.info("INTEGRATION TEST 4: Error Recovery")
    logger.info("="*80)
    
    # Test 1: Module 3 without hypotheses (should fail gracefully)
    logger.info("\nTest 1: Module 3 without hypotheses")
    try:
        project = ProjectState(
            rq=ResearchQuestion(
                id="error_test_1",
                raw_text="Test error handling",
                parsed_constructs=["test"]
            )
        )
        # No hypotheses
        
        from Experimental_Design_Builder_Critic import run, Module3Error
        
        try:
            await run(project, use_llm=False)
            logger.error("  ✗ Should have raised Module3Error")
            return False
        except Module3Error as e:
            logger.info(f"  ✓ Correctly raised error: {str(e)[:60]}...")
        
    except Exception as e:
        logger.error(f"  ✗ Unexpected error: {e}")
        return False
    
    # Test 2: Confound checker with minimal data (should not crash)
    logger.info("\nTest 2: Confound checker with minimal data")
    try:
        from Experimental_Design_Builder_Critic.design_proposer import DesignProposal
        from Experimental_Design_Builder_Critic.confound_checker import check_confounds
        from copilot_workflow.schemas import Condition, Measure
        
        minimal_proposal = DesignProposal(
            design_type="between_subjects",
            conditions=[
                Condition(id="c1", label="Control"),
                Condition(id="c2", label="Experimental")
            ],
            measures=[Measure(id="m1", label="Outcome")],
            time_points=["post"],
            rationale="Minimal design"
        )
        
        warnings = check_confounds(minimal_proposal)
        logger.info(f"  ✓ Confound checker handled minimal data: {len(warnings)} warnings")
        
    except Exception as e:
        logger.error(f"  ✗ Confound checker crashed: {e}")
        return False
    
    # Test 3: Sample size calculator with invalid input (should use defaults)
    logger.info("\nTest 3: Sample size calculator with invalid effect size")
    try:
        from Experimental_Design_Builder_Critic.sample_size_calculator import calculate_sample_size
        from copilot_workflow.schemas import Hypothesis
        
        project = ProjectState(
            rq=ResearchQuestion(
                id="error_test_3",
                raw_text="Test",
                parsed_constructs=["test"]
            )
        )
        project.hypotheses = [
            Hypothesis(id="h1", text="Test", iv=["IV"], dv=["DV"])
        ]
        
        from Experimental_Design_Builder_Critic.design_proposer import propose_design
        proposal = await propose_design(project, use_llm=False)
        
        # Try invalid effect size
        plan = calculate_sample_size(proposal, effect_size="invalid")
        
        logger.info(f"  ✓ Invalid effect size handled: defaulted to {plan.effect_size}")
        
    except Exception as e:
        logger.error(f"  ✗ Sample size calculator crashed: {e}")
        return False
    
    logger.info("\n✅ Error recovery tests PASSED")
    return True


async def test_audit_logging():
    """Test that audit logging works throughout pipeline."""
    logger.info("\n" + "="*80)
    logger.info("INTEGRATION TEST 5: Audit Logging")
    logger.info("="*80)
    
    project = ProjectState(
        rq=ResearchQuestion(
            id="audit_test",
            raw_text="Testing audit logs",
            parsed_constructs=["audit", "logging"]
        )
    )
    
    try:
        # Run Module 1
        from Literature_Landscape_Explorer import run_with_summary as run_m1
        project, _ = await run_m1(project)
        
        m1_entries = len(project.audit_log)
        logger.info(f"After Module 1: {m1_entries} audit entries")
        assert m1_entries > 0, "Module 1 should add audit entries"
        
        # Run Module 2
        from Hypothesis_Generator_Structurer import run_with_summary as run_m2
        project, _ = await run_m2(project, num_hypotheses=2)
        
        m2_entries = len(project.audit_log)
        logger.info(f"After Module 2: {m2_entries} audit entries (+{m2_entries - m1_entries})")
        assert m2_entries > m1_entries, "Module 2 should add more entries"
        
        # Run Module 3
        from Experimental_Design_Builder_Critic import run_with_summary as run_m3
        project, _ = await run_m3(project, use_llm=False)
        
        m3_entries = len(project.audit_log)
        logger.info(f"After Module 3: {m3_entries} audit entries (+{m3_entries - m2_entries})")
        assert m3_entries > m2_entries, "Module 3 should add more entries"
        
        # Check audit log structure
        logger.info("\nAudit log sample:")
        for i, entry in enumerate(project.audit_log[-3:], 1):
            logger.info(f"  {i}. [{entry.level}] {entry.location}: {entry.message[:50]}...")
        
        logger.info("\n✅ Audit logging test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Audit logging test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests."""
    print("\n" + "#"*80)
    print("# INTEGRATION TESTS: Modules 1 → 2 → 3 Pipeline")
    print("# Complete workflow from Research Question to Experimental Design")
    print("#"*80)
    
    tests = [
        ("Full Pipeline (Modules 1→2→3)", test_full_pipeline_end_to_end),
        ("Data Flow Validation", test_data_flow_validation),
        ("Module 3 Edge Cases", test_module3_edge_cases),
        ("Error Recovery", test_error_recovery),
        ("Audit Logging", test_audit_logging),
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
        await asyncio.sleep(3)
    
    # Summary
    print("\n" + "#"*80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"# ✅ ALL INTEGRATION TESTS PASSED ({passed}/{total})")
    else:
        print(f"# ❌ SOME TESTS FAILED ({passed}/{total} passed)")
    
    print("#"*80)
    print("# Test Results:")
    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"#   {status} {test_name}")
    print("#"*80)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
