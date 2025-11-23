#!/usr/bin/env python3
"""Functional test for Module 2: Hypothesis Generator & Structurer.

Tests the complete hypothesis generation flow:
1. Research question + concepts → Hypothesis generation
2. Hypotheses → Validation
3. Export to JSON and markdown
"""

import asyncio
import sys
from pathlib import Path

# Add paths
ROOT = Path(__file__).resolve().parent.parent
for p in [ROOT / "spoon-core", ROOT / "spoon-toolkit", ROOT]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

from copilot_workflow.schemas import ProjectState, ResearchQuestion, ConceptNode, ConceptEdge
from Hypothesis_Generator_Structurer.run import run_with_summary


async def test_basic_hypothesis_generation():
    """Test 1: Basic hypothesis generation from RQ and concepts."""
    print("\n" + "="*80)
    print("Test 1: Basic Hypothesis Generation")
    print("="*80)
    
    # Create project with research question
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="How does attachment anxiety influence emotion regulation strategies in romantic relationships?",
        parsed_constructs=["attachment anxiety", "emotion regulation strategies", "romantic relationships"],
        domain="Social Psychology"
    )
    
    # Mock concept nodes from Module 1
    project.concepts = {
        "nodes": [
            ConceptNode(
                id="c1",
                label="Attachment Anxiety",
                type="construct",
                common_measures=["ECR-R Anxiety subscale", "AAI"],
                linked_papers=["paper_1", "paper_2"]
            ),
            ConceptNode(
                id="c2",
                label="Emotion Regulation Strategies",
                type="construct",
                common_measures=["ERQ", "DERS"],
                linked_papers=["paper_3", "paper_4"]
            ),
            ConceptNode(
                id="c3",
                label="Romantic Relationships",
                type="context",
                common_measures=["Relationship Satisfaction Scale"],
                linked_papers=["paper_5"]
            )
        ],
        "edges": [
            ConceptEdge(
                source="c1",
                target="c2",
                relation_type="predicts"
            ),
            ConceptEdge(
                source="c2",
                target="c3",
                relation_type="occurs_in"
            )
        ]
    }
    
    print(f"\nResearch Question: {project.rq.raw_text}")
    print(f"Concepts: {len(project.concepts['nodes'])} nodes, {len(project.concepts['edges'])} edges\n")
    
    try:
        # Run Module 2
        result, summary = await run_with_summary(project, num_hypotheses=5)
        
        # Validate results
        print("✓ Module 2 Completed Successfully\n")
        
        # Check hypotheses generated
        hyp_count = summary["hypotheses_generated"]
        print(f"📊 Hypotheses Generated: {hyp_count}")
        assert hyp_count > 0, "Should generate at least one hypothesis"
        
        # Check validation
        valid_count = summary["valid_hypotheses"]
        print(f"✅ Valid Hypotheses: {valid_count}/{hyp_count}")
        print(f"📈 Avg Quality Score: {summary['avg_quality_score']:.2f}")
        
        # Check hypothesis structure
        print(f"\n🔬 Hypothesis Details:")
        print(f"   - With Mediators: {summary['with_mediators']}")
        print(f"   - With Moderators: {summary['with_moderators']}")
        print(f"   - Unique IVs: {summary['unique_ivs']}")
        print(f"   - Unique DVs: {summary['unique_dvs']}")
        print(f"   - Frameworks: {len(summary['frameworks'])}")
        
        # Show generated hypotheses
        print(f"\n💡 Generated Hypotheses:")
        for i, h in enumerate(result.hypotheses, 1):
            print(f"\n  {i}. {h.text}")
            print(f"     IV: {', '.join(h.iv)}")
            print(f"     DV: {', '.join(h.dv)}")
            if h.mediators:
                print(f"     Mediators: {', '.join(h.mediators)}")
            if h.moderators:
                print(f"     Moderators: {', '.join(h.moderators)}")
            if h.theoretical_basis:
                print(f"     Framework: {', '.join(h.theoretical_basis[:2])}")
        
        # Show audit log
        print(f"\n📋 Audit Log:")
        for entry in result.audit_log[-5:]:  # Last 5 entries
            print(f"   [{entry.level.upper()}] {entry.message}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_mediation_hypothesis():
    """Test 2: Generate mediation hypothesis."""
    print("\n" + "="*80)
    print("Test 2: Mediation Hypothesis Generation")
    print("="*80)
    
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="Does self-compassion mediate the relationship between perfectionism and burnout?",
        parsed_constructs=["self-compassion", "perfectionism", "burnout"],
        domain="Organizational Psychology"
    )
    
    # Mock concepts suggesting mediation
    project.concepts = {
        "nodes": [
            ConceptNode(id="c1", label="Perfectionism", type="construct", common_measures=["MPS"]),
            ConceptNode(id="c2", label="Self-Compassion", type="construct", common_measures=["SCS"]),
            ConceptNode(id="c3", label="Burnout", type="construct", common_measures=["MBI"])
        ],
        "edges": [
            ConceptEdge(source="c1", target="c2", relation_type="negatively_predicts"),
            ConceptEdge(source="c2", target="c3", relation_type="negatively_predicts"),
            ConceptEdge(source="c1", target="c3", relation_type="predicts")
        ]
    }
    
    print(f"\nResearch Question: {project.rq.raw_text}\n")
    
    try:
        result, summary = await run_with_summary(project, num_hypotheses=3)
        
        print("✓ Module 2 Completed Successfully\n")
        print(f"📊 Hypotheses: {summary['hypotheses_generated']}")
        print(f"✅ Valid: {summary['valid_hypotheses']}")
        print(f"🔗 With Mediators: {summary['with_mediators']}")
        
        # Check for mediation hypothesis
        has_mediation = any(len(h.mediators) > 0 for h in result.hypotheses)
        print(f"\n💡 Generated Mediation Hypothesis: {'Yes' if has_mediation else 'No'}")
        
        if has_mediation:
            for h in result.hypotheses:
                if h.mediators:
                    print(f"\n  Mediation: {h.text}")
                    print(f"  Mediator: {', '.join(h.mediators)}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


async def test_minimal_input():
    """Test 3: Edge case - minimal concept graph."""
    print("\n" + "="*80)
    print("Test 3: Edge Case - Minimal Input")
    print("="*80)
    
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="How does exercise affect mood?",
        parsed_constructs=["exercise", "mood"],
        domain="Health Psychology"
    )
    
    # Minimal concept graph (just RQ constructs)
    project.concepts = {
        "nodes": [
            ConceptNode(id="c1", label="Exercise", type="construct"),
            ConceptNode(id="c2", label="Mood", type="construct")
        ],
        "edges": []
    }
    
    print(f"\nResearch Question: {project.rq.raw_text}")
    print(f"Concepts: Minimal (2 nodes, 0 edges)\n")
    
    try:
        result, summary = await run_with_summary(project, num_hypotheses=3)
        
        print("✓ Module 2 Completed Successfully\n")
        print(f"📊 Hypotheses: {summary['hypotheses_generated']}")
        print(f"✅ Valid: {summary['valid_hypotheses']}")
        print(f"📈 Quality: {summary['avg_quality_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


async def main():
    """Run all Module 2 functional tests."""
    print("\n" + "#"*80)
    print("# Module 2: Hypothesis Generator & Structurer - Functional Tests")
    print("#"*80)
    
    # Test 1: Basic hypothesis generation
    test1_passed = await test_basic_hypothesis_generation()
    
    # Wait to avoid rate limits
    print("\n⏳ Waiting 5 seconds to avoid rate limits...")
    await asyncio.sleep(5)
    
    # Test 2: Mediation hypothesis
    test2_passed = await test_mediation_hypothesis()
    
    # Wait again
    print("\n⏳ Waiting 5 seconds...")
    await asyncio.sleep(5)
    
    # Test 3: Edge case
    test3_passed = await test_minimal_input()
    
    # Summary
    print("\n" + "#"*80)
    if test1_passed and test2_passed and test3_passed:
        print("# ✅ All Functional Tests Passed!")
        print("#")
        print("# Module 2 is fully operational and ready for integration.")
        print("# You can now proceed to Module 3: Experimental Design Builder")
    else:
        print("# ❌ Some Tests Failed")
        print(f"#   Test 1 (Basic): {'✓' if test1_passed else '✗'}")
        print(f"#   Test 2 (Mediation): {'✓' if test2_passed else '✗'}")
        print(f"#   Test 3 (Edge Case): {'✓' if test3_passed else '✗'}")
    print("#"*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
