"""Standalone test script for Google Scholar search."""

import asyncio
import aiohttp
import os


async def test_serpapi():
    """Test SerpAPI Google Scholar search directly."""
    api_key = "6048a0b8e1e187e5301793e9500025d462768faaad666d516c17d0b97bad587e"
    url = "https://serpapi.com/search"
    
    params = {
        "engine": "google_scholar",
        "q": "cognitive flexibility mindfulness meditation",
        "api_key": api_key,
        "num": 5,
        "hl": "en"
    }
    
    print("Testing SerpAPI Google Scholar search...")
    print(f"Query: {params['q']}\n")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                print(f"❌ Error: Status {response.status}")
                return
            
            data = await response.json()
            
            # Check for results
            organic_results = data.get("organic_results", [])
            print(f"✅ Found {len(organic_results)} papers\n")
            
            # Display first 3 papers
            for i, result in enumerate(organic_results[:3], 1):
                print(f"{i}. {result.get('title', 'No title')}")
                pub_info = result.get('publication_info', {})
                print(f"   Authors: {pub_info.get('authors', 'N/A')}")
                print(f"   Summary: {pub_info.get('summary', 'N/A')}")
                cited_by = result.get('inline_links', {}).get('cited_by', {}).get('total', 0)
                print(f"   Cited by: {cited_by}")
                print(f"   Link: {result.get('link', 'N/A')}")
                print()


if __name__ == "__main__":
    asyncio.run(test_serpapi())
