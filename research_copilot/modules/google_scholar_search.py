"""Google Scholar search using SerpAPI.

Fast academic paper search using SerpAPI's Google Scholar endpoint.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)

# Get API key from environment
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "6048a0b8e1e187e5301793e9500025d462768faaad666d516c17d0b97bad587e")
SERPAPI_BASE_URL = "https://serpapi.com/search"


async def search_google_scholar(
    query: str,
    num_results: int = 10,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Search Google Scholar using SerpAPI.
    
    Args:
        query: Search query string
        num_results: Number of results to return (1-20)
        year_from: Optional year to start search from
        year_to: Optional year to end search at
        
    Returns:
        List of paper dictionaries with title, authors, year, url, snippet
    """
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": min(num_results, 20),  # Max 20 per request
        "hl": "en"
    }
    
    # Add year filters if provided
    if year_from:
        params["as_ylo"] = year_from
    if year_to:
        params["as_yhi"] = year_to
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SERPAPI_BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"SerpAPI request failed with status {response.status}")
                    return []
                
                data = await response.json()
                
                # Parse organic results
                papers = []
                for result in data.get("organic_results", []):
                    paper = {
                        "title": result.get("title", ""),
                        "authors": result.get("publication_info", {}).get("authors", []),
                        "year": extract_year(result.get("publication_info", {}).get("summary", "")),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "cited_by": result.get("inline_links", {}).get("cited_by", {}).get("total", 0),
                        "source": "Google Scholar"
                    }
                    papers.append(paper)
                
                logger.info(f"Found {len(papers)} papers for query: {query}")
                return papers
                
    except Exception as e:
        logger.error(f"Error searching Google Scholar: {e}")
        return []


def extract_year(summary: str) -> str:
    """Extract publication year from summary string.
    
    Args:
        summary: Publication info summary
        
    Returns:
        Year as string, or empty string if not found
    """
    import re
    if not summary:
        return ""
    
    # Look for 4-digit year
    match = re.search(r'\b(19|20)\d{2}\b', summary)
    return match.group(0) if match else ""


async def search_multiple_queries(
    queries: List[str],
    papers_per_query: int = 10
) -> Dict[str, Any]:
    """Search multiple queries and combine results.
    
    Args:
        queries: List of search queries
        papers_per_query: Number of papers per query
        
    Returns:
        Dictionary with combined papers and citations
    """
    all_papers = []
    all_citations = []
    
    for query in queries:
        papers = await search_google_scholar(query, num_results=papers_per_query)
        all_papers.extend(papers)
        
        # Convert to citation format
        for paper in papers:
            citation = {
                "title": paper["title"],
                "authors": ", ".join(paper["authors"]) if isinstance(paper["authors"], list) else paper["authors"],
                "year": paper["year"],
                "url": paper["url"]
            }
            all_citations.append(citation)
    
    return {
        "papers": all_papers,
        "citations": all_citations[:20]  # Limit citations
    }
