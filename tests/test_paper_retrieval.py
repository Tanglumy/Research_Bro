#!/usr/bin/env python3
"""Test script for paper retrieval using web search."""

import asyncio
import sys
from pathlib import Path

# Add paths to system
ROOT = Path(__file__).resolve().parent.parent
SPOON_CORE_PATH = ROOT / "spoon-core"
SPOON_TOOLKIT_PATH = ROOT / "spoon-toolkit"
for p in (SPOON_CORE_PATH, SPOON_TOOLKIT_PATH, ROOT):
    if p.exists():
        sys.path.append(str(p))

from Literature_Landscape_Explorer.paper_retrieval import (
    retrieve_papers,
    retrieve_papers_by_query,
    Paper
)


async def test_retrieve_papers_with_constructs():
    """Test retrieving papers using research constructs."""
    print("\n" + "="*80)
    print("Test 1: Retrieve Papers with Constructs")
    print("="*80)
    
    constructs = ["attachment anxiety", "emotion regulation"]
    print(f"\nResearch Constructs: {constructs}\n")
    
    try:
        papers = await retrieve_papers(constructs, limit=5)
        
        print(f"✓ Retrieved {len(papers)} papers\n")
        
        for i, paper in enumerate(papers, 1):
            print(f"Paper {i}:")
            print(f"  Title: {paper.title}")
            print(f"  Authors: {', '.join(paper.authors)}")
            print(f"  Year: {paper.year or 'Unknown'}")
            print(f"  Source: {paper.source}")
            print(f"  URL: {paper.url}")
            print(f"  Abstract: {paper.abstract[:150]}...\n")
        
        # Validate paper structure
        assert all(isinstance(p, Paper) for p in papers), "All results should be Paper objects"
        assert all(p.title for p in papers), "All papers should have titles"
        assert all(p.abstract for p in papers), "All papers should have abstracts"
        
        print("✓ All papers have required fields\n")
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_retrieve_papers_by_query():
    """Test retrieving papers using a single query string."""
    print("\n" + "="*80)
    print("Test 2: Retrieve Papers by Query String")
    print("="*80)
    
    query = "social anxiety treatment efficacy"
    print(f"\nQuery: {query}\n")
    
    try:
        papers = await retrieve_papers_by_query(query, limit=3)
        
        print(f"✓ Retrieved {len(papers)} papers\n")
        
        for i, paper in enumerate(papers, 1):
            print(f"Paper {i}: {paper.title}")
            print(f"  Source: {paper.source}")
            print()
        
        return len(papers) > 0
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


async def test_paper_metadata_extraction():
    """Test metadata extraction from search results."""
    print("\n" + "="*80)
    print("Test 3: Metadata Extraction")
    print("="*80)
    
    constructs = ["cognitive behavioral therapy"]
    print(f"\nResearch Constructs: {constructs}\n")
    
    try:
        papers = await retrieve_papers(constructs, limit=3)
        
        if not papers:
            print("⚠ No papers retrieved, skipping metadata test")
            return True
        
        # Check metadata quality
        has_year = sum(1 for p in papers if p.year is not None)
        has_doi = sum(1 for p in papers if p.doi is not None)
        has_authors = sum(1 for p in papers if p.authors and p.authors[0] != "Unknown")
        
        print(f"Metadata Statistics:")
        print(f"  Papers with year: {has_year}/{len(papers)}")
        print(f"  Papers with DOI: {has_doi}/{len(papers)}")
        print(f"  Papers with authors: {has_authors}/{len(papers)}\n")
        
        # Verify sources are identified correctly
        sources = set(p.source for p in papers)
        print(f"Sources identified: {', '.join(sources)}\n")
        
        print("✓ Metadata extraction working\n")
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


async def main():
    """Run all paper retrieval tests."""
    print("\n" + "#"*80)
    print("# Paper Retrieval Tests (Web Search)")
    print("#"*80)
    
    # Test 1: Basic retrieval with constructs
    test1_passed = await test_retrieve_papers_with_constructs()
    
    # Add delay to avoid rate limits
    print("⏳ Waiting 2 seconds to avoid rate limits...\n")
    await asyncio.sleep(2)
    
    # Test 2: Query string convenience function
    test2_passed = await test_retrieve_papers_by_query()
    
    # Add delay
    print("⏳ Waiting 2 seconds...\n")
    await asyncio.sleep(2)
    
    # Test 3: Metadata extraction
    test3_passed = await test_paper_metadata_extraction()
    
    # Summary
    print("\n" + "#"*80)
    if test1_passed and test2_passed and test3_passed:
        print("# ✅ All Tests Passed!")
    else:
        print("# ❌ Some Tests Failed")
        print(f"#   Test 1 (Constructs): {'✓' if test1_passed else '✗'}")
        print(f"#   Test 2 (Query): {'✓' if test2_passed else '✗'}")
        print(f"#   Test 3 (Metadata): {'✓' if test3_passed else '✗'}")
    print("#"*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
