#!/usr/bin/env python3
"""Test script for Gemini API and research question ingestion."""

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

from spoon_ai.llm import LLMManager, ConfigurationManager
from spoon_ai.schema import Message
from copilot_workflow.workflow import run_workflow


async def test_gemini_api():
    """Test 0: Verify Gemini API key works."""
    print("\n" + "="*80)
    print("Test 0: Gemini API Connection")
    print("="*80)
    
    try:
        llm = LLMManager(ConfigurationManager())
        msg = [Message(role="user", content="Say hello in one word")]
        response = await llm.chat(msg, provider="gemini")
        
        print("\n✓ Gemini API Connected Successfully")
        print(f"Response: {response.content}\n")
        return True
    except Exception as e:
        print(f"\n✗ Gemini API Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_construct_extraction():
    """Test 1: Test Gemini's ability to extract research constructs."""
    print("\n" + "="*80)
    print("Test 1: Gemini Construct Extraction")
    print("="*80)
    
    test_query = "How does attachment anxiety influence emotion regulation strategies?"
    print(f"\nInput: {test_query}\n")
    
    try:
        llm = LLMManager(ConfigurationManager())
        
        prompt = f"""Analyze this research question and extract key psychological/behavioral constructs:

Question: {test_query}

Provide:
1. Main constructs (2-5 key concepts that are central to the research)
2. Research domain (e.g., emotion regulation, attachment, social cognition, decision-making)
3. Potential independent variables (what might be manipulated or compared)
4. Potential dependent variables (what might be measured as outcomes)

Return ONLY valid JSON in this exact format:
{{
  "constructs": ["construct1", "construct2", ...],
  "domain": "research domain",
  "potential_iv": ["var1", "var2"],
  "potential_dv": ["var1", "var2"]
}}"""
        
        response = await llm.chat(
            [Message(role="user", content=prompt)],
            provider="gemini"
        )
        
        # Debug: Show raw response
        print(f"Raw Gemini Response:\n{response.content}\n")
        
        import json
        # Strip markdown code fences if present
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed_data = json.loads(content)
        
        print("✓ Gemini Successfully Extracted Constructs\n")
        print(f"Constructs: {parsed_data.get('constructs')}")
        print(f"Domain: {parsed_data.get('domain')}")
        print(f"Potential IVs: {parsed_data.get('potential_iv')}")
        print(f"Potential DVs: {parsed_data.get('potential_dv')}\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Construct Extraction Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_workflow():
    """Test 2: Test full workflow with basic psychology research question."""
    print("\n" + "="*80)
    print("Test 2: Full Workflow - Basic Psychology Question")
    print("="*80)
    
    query = "How does attachment anxiety influence emotion regulation strategies in romantic relationships?"
    print(f"\nInput: {query}\n")
    
    try:
        result = await run_workflow(query)
        project = result.get("project")
        
        if project and project.rq:
            print("✓ Research Question Created Successfully\n")
            print(f"Raw Text: {project.rq.raw_text}")
            print(f"\nExtracted Constructs: {project.rq.parsed_constructs}")
            print(f"Domain: {project.rq.domain}")
            print(f"Notes: {project.rq.notes}")
            
            # Check audit log
            if project.audit_log:
                print("\n--- Audit Log ---")
                for entry in project.audit_log:
                    print(f"[{entry.level.upper()}] {entry.message}")
                    if entry.details:
                        print(f"  Details: {entry.details}")
            return True
        else:
            print("✗ Failed to create research question")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests sequentially: API -> Construct Extraction -> Full Workflow."""
    print("\n" + "#"*80)
    print("# Gemini API & Research Question Ingestion Tests")
    print("#"*80)
    
    # Test 0: Verify Gemini API works
    api_works = await test_gemini_api()
    if not api_works:
        print("\n❌ Gemini API not working. Stopping tests.")
        return
    
    # Test 1: Test construct extraction specifically
    extraction_works = await test_gemini_construct_extraction()
    if not extraction_works:
        print("\n❌ Construct extraction failed. Check Gemini response format.")
        return
    
    # Test 2: Full workflow integration
    print("\n⏳ Waiting 3 seconds to avoid rate limits...")
    await asyncio.sleep(3)
    workflow_works = await test_basic_workflow()
    
    print("\n" + "#"*80)
    if api_works and extraction_works and workflow_works:
        print("# ✅ All Tests Passed!")
    else:
        print("# ❌ Some Tests Failed")
    print("#"*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
