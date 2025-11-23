"""Paper retrieval using web search for academic papers.

Retrieves academic papers from various sources (Google Scholar, PubMed, arXiv)
using the WebSearchTool and provides structured metadata for downstream analysis.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests library not available. Paper retrieval will be limited.")

from copilot_workflow.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """Structured paper metadata."""
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str = "web_search"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "year": self.year,
            "doi": self.doi,
            "url": self.url,
            "source": self.source,
        }


class PaperRetrievalError(Exception):
    """Raised when paper retrieval fails."""
    pass


async def retrieve_papers(
    constructs: List[str],
    limit: int = 20,
    max_retries: Optional[int] = None
) -> List[Paper]:
    """Retrieve academic papers using research constructs.
    
    Uses OpenAlex API to find relevant papers. OpenAlex is a free, open catalog
    of scholarly papers with comprehensive metadata.
    
    Args:
        constructs: List of research constructs to search for
        limit: Maximum number of papers to retrieve (default: 20)
        max_retries: Override default retry count from config
        
    Returns:
        List of Paper objects with metadata
        
    Raises:
        PaperRetrievalError: If retrieval fails after retries
    """
    config = get_config()
    
    # Check if requests is available
    if not REQUESTS_AVAILABLE:
        logger.warning("requests library not available")
        return []
    
    # Build search query from constructs
    query = " ".join(constructs)
    logger.info(f"Searching OpenAlex for papers with query: {query}")
    
    # Get retry configuration
    retry_config = config.get_retry_config()
    max_retries = max_retries or retry_config["max_retries"]
    retry_delay = retry_config["retry_delay"]
    
    # Attempt retrieval with retries
    for attempt in range(max_retries):
        try:
            papers = await _fetch_papers_from_openalex(query, limit=limit)
            logger.info(f"Retrieved {len(papers)} papers from OpenAlex")
            return papers
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(
                    f"OpenAlex retrieval attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"OpenAlex retrieval failed after {max_retries} attempts: {e}")
                raise PaperRetrievalError(f"Failed to retrieve papers: {e}")
    
    return []


async def _fetch_papers_from_openalex(query: str, limit: int) -> List[Paper]:
    """Fetch papers from OpenAlex API.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of Paper objects
    """
    # OpenAlex API endpoint
    url = "https://api.openalex.org/works"
    
    # Build query parameters
    params = {
        "search": query,
        "per_page": min(limit, 50),  # OpenAlex max is 50 per page
        "filter": "type:article",  # Only articles
        "sort": "cited_by_count:desc",  # Most cited first
        "mailto": "contact@sylph.ai"  # Polite pool (faster response)
    }
    
    # Make request
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    # Parse results
    papers = []
    for work in data.get("results", []):
        try:
            paper = _parse_openalex_work(work)
            if paper:
                papers.append(paper)
        except Exception as e:
            logger.warning(f"Failed to parse OpenAlex work: {e}")
            continue
    
    return papers


def _parse_openalex_work(work: Dict[str, Any]) -> Optional[Paper]:
    """Parse OpenAlex work into Paper object.
    
    Args:
        work: Raw work data from OpenAlex API
        
    Returns:
        Paper object or None if parsing fails
    """
    # Extract title
    title = work.get("title", "").strip()
    if not title:
        return None
    
    # Extract abstract (inverted index format)
    abstract = ""
    abstract_inverted = work.get("abstract_inverted_index")
    if abstract_inverted:
        # Reconstruct abstract from inverted index
        abstract = _reconstruct_abstract(abstract_inverted)
    
    # If no abstract, use title as proxy
    if not abstract:
        abstract = title
    
    # Extract authors
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name")
        if name:
            authors.append(name)
    
    if not authors:
        authors = ["Unknown"]
    
    # Extract year
    year = work.get("publication_year")
    
    # Extract DOI
    doi = work.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    
    # Extract URL
    url = work.get("doi") or work.get("id")
    
    return Paper(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        doi=doi,
        url=url,
        source="openalex"
    )


def _reconstruct_abstract(inverted_index: Dict[str, List[int]]) -> str:
    """Reconstruct abstract from OpenAlex inverted index format.
    
    OpenAlex stores abstracts as inverted index: {word: [positions]}.
    This function reconstructs the original text.
    
    Args:
        inverted_index: Dictionary mapping words to position lists
        
    Returns:
        Reconstructed abstract text
    """
    if not inverted_index:
        return ""
    
    # Find max position to determine length
    max_pos = 0
    for positions in inverted_index.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    
    # Build array of words
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    
    # Join into text
    abstract = " ".join(words)
    
    # Truncate if too long
    if len(abstract) > 2000:
        abstract = abstract[:2000] + "..."
    
    return abstract





def _deduplicate_papers(papers: List[Paper]) -> List[Paper]:
    """Remove duplicate papers based on title similarity.
    
    Args:
        papers: List of papers potentially with duplicates
        
    Returns:
        List of unique papers
    """
    unique_papers = []
    seen_titles = set()
    
    for paper in papers:
        # Normalize title for comparison
        normalized_title = paper.title.lower().strip()
        
        if normalized_title not in seen_titles:
            unique_papers.append(paper)
            seen_titles.add(normalized_title)
    
    return unique_papers


async def retrieve_papers_by_query(
    query: str,
    limit: int = 20
) -> List[Paper]:
    """Convenience function to retrieve papers using a single query string.
    
    Args:
        query: Natural language search query
        limit: Maximum number of papers
        
    Returns:
        List of Paper objects
    """
    return await retrieve_papers([query], limit=limit)
