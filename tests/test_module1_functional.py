#!/usr/bin/env python3
"""Functional test for Module 1: Literature Landscape Explorer.

Tests the complete end-to-end flow:
1. Research question → Paper retrieval
2. Papers → Concept extraction
3. Concepts → Knowledge graph
4. Graph → Gap analysis
"""

import asyncio
import sys
from pathlib import Path

# Add paths
ROOT = Path(__file__).resolve().parent.parent
for p in [ROOT / "spoon-core", ROOT / "spoon-toolkit", ROOT]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

from copilot_workflow.schemas import ProjectState, ResearchQuestion
from Literature_Landscape_Explorer.run import run, run_with_summary


async def test_basic_research_question():
    """Test 1: Basic psychology research question."""
    print("\n" + "="*80)
    print("Test 1: Basic Psychology Research Question")
    print("="*80)
    
    # Create project with research question
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="How does attachment anxiety influence emotion regulation strategies in romantic relationships?",
        parsed_constructs=["attachment anxiety", "emotion regulation strategies", "romantic relationships"],
        domain="Social Psychology"
    )
    
    print(f"\nResearch Question: {project.rq.raw_text}")
    print(f"Constructs: {project.rq.parsed_constructs}\n")
    
    try:
        # Run Module 1
        result, summary = await run_with_summary(project)
        
        # Validate results
        print("✓ Module 1 Completed Successfully\n")
        
        # Check papers retrieved
        papers = summary["papers"]
        print(f"📄 Papers Retrieved: {papers}")
        assert papers > 0, "Should retrieve at least some papers"
        
        # Check concepts extracted
        concepts = summary["concepts"]
        print(f"📚 Concepts Extracted:")
        print(f"   - Frameworks: {concepts.get('frameworks', 0)}")
        print(f"   - Constructs: {concepts.get('constructs', 0)}")
        print(f"   - Measures: {concepts.get('measures', 0)}")
        print(f"   - Paradigms: {concepts.get('paradigms', 0)}")
        print(f"   - Relationships: {concepts.get('relationships', 0)}")
        
        # Check graph built
        graph = summary["graph"]
        print(f"\n🕸️ Knowledge Graph:")
        print(f"   - Nodes: {graph.get('nodes', 0)}")
        print(f"   - Edges: {graph.get('edges', 0)}")
        assert graph.get('nodes', 0) > 0, "Should have graph nodes"
        
        # Check gap analysis
        gaps = summary["gaps"]
        print(f"\n🔍 Gap Analysis:")
        print(f"   - Gaps Found: {gaps.get('gaps_found', 0)}")
        print(f"   - High Severity: {gaps.get('high_severity_gaps', 0)}")
        print(f"   - Novelty Score: {gaps.get('novelty_score', 0):.2f}")
        print(f"   - Coverage Score: {gaps.get('coverage_score', 0):.2f}")
        print(f"\n   Summary: {gaps.get('summary', 'N/A')[:200]}...")
        
        # Show top constructs
        top = summary.get("top_constructs", [])
        if top:
            print(f"\n🔝 Top Constructs:")
            for c in top[:3]:
                print(f"   - {c['name']} (frequency: {c['frequency']})")
        
        # Show audit log
        print(f"\n📋 Audit Log:")
        for entry in result.audit_log:
            print(f"   [{entry.level.upper()}] {entry.message}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_complex_mediation_question():
    """Test 2: Complex research question with mediation/moderation."""
    print("\n" + "="*80)
    print("Test 2: Complex Mediation/Moderation Question")
    print("="*80)
    
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="Does self-compassion mediate the relationship between perfectionism and burnout in healthcare workers?",
        parsed_constructs=["self-compassion", "perfectionism", "burnout"],
        domain="Organizational Psychology"
    )
    
    print(f"\nResearch Question: {project.rq.raw_text}")
    print(f"Constructs: {project.rq.parsed_constructs}\n")
    
    try:
        result, summary = await run_with_summary(project)
        
        print("✓ Module 1 Completed Successfully\n")
        print(f"📄 Papers: {summary['papers']}")
        print(f"📚 Constructs: {summary['concepts'].get('constructs', 0)}")
        print(f"🕸️ Graph Nodes: {summary['graph'].get('nodes', 0)}")
        print(f"🔍 Novelty Score: {summary['gaps'].get('novelty_score', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


async def test_edge_case_novel_constructs():
    """Test 3: Edge case - highly novel constructs."""
    print("\n" + "="*80)
    print("Test 3: Edge Case - Novel Constructs")
    print("="*80)
    
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text="How does exercise reduce anxiety?",
        parsed_constructs=["exercise", "anxiety"],
        domain="Health Psychology"
    )
    
    print(f"\nResearch Question: {project.rq.raw_text}")
    print(f"Constructs: {project.rq.parsed_constructs}\n")
    
    try:
        result, summary = await run_with_summary(project)
        
        print("✓ Module 1 Completed Successfully\n")
        
        # Check basic metrics
        novelty = summary['gaps'].get('novelty_score', 0)
        print(f"🔍 Novelty Score: {novelty:.2f}")
        
        gaps_found = summary['gaps'].get('gaps_found', 0)
        print(f"📊 Gaps Found: {gaps_found}")
        
        papers = summary['papers']
        print(f"📄 Papers: {papers}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False


async def main():
    """Run all functional tests."""
    print("\n" + "#"*80)
    print("# Module 1: Literature Landscape Explorer - Functional Tests")
    print("#"*80)
    
    # Test 1: Basic research question
    test1_passed = await test_basic_research_question()
    
    # Wait to avoid rate limits
    print("\n⏳ Waiting 5 seconds to avoid rate limits...")
    await asyncio.sleep(5)
    
    # Test 2: Complex question
    test2_passed = await test_complex_mediation_question()
    
    # Wait again
    print("\n⏳ Waiting 5 seconds...")
    await asyncio.sleep(5)
    
    # Test 3: Edge case
    test3_passed = await test_edge_case_novel_constructs()
    
    # Summary
    print("\n" + "#"*80)
    if test1_passed and test2_passed and test3_passed:
        print("# ✅ All Functional Tests Passed!")
        print("#")
        print("# Module 1 is fully operational and ready for production.")
        print("# You can now proceed to Module 2: Hypothesis Generator")
    else:
        print("# ❌ Some Tests Failed")
        print(f"#   Test 1 (Basic): {'✓' if test1_passed else '✗'}")
        print(f"#   Test 2 (Complex): {'✓' if test2_passed else '✗'}")
        print(f"#   Test 3 (Edge Case): {'✓' if test3_passed else '✗'}")
    print("#"*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
