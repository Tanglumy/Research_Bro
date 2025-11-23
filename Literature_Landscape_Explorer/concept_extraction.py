"""Concept extraction from academic papers using Gemini.

Analyzes paper abstracts to extract:
- Theoretical frameworks
- Research constructs
- Measurement instruments
- Experimental paradigms
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Set
from dataclasses import dataclass

try:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    for p in [root / "spoon-core", root / "spoon-toolkit"]:
        if p.exists() and str(p) not in sys.path:
            sys.path.append(str(p))
    
    from spoon_ai.llm import LLMManager, ConfigurationManager
    from spoon_ai.schema import Message
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("LLM tools not available. Concept extraction will be limited.")

from copilot_workflow.config import get_config
from Literature_Landscape_Explorer.paper_retrieval import Paper

logger = logging.getLogger(__name__)


@dataclass
class ExtractedConcept:
    """A concept extracted from literature."""
    name: str
    type: str  # "construct", "framework", "measure", "paradigm"
    description: str
    papers: List[str]  # Paper titles that mention this concept
    frequency: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "papers": self.papers,
            "frequency": self.frequency,
        }


@dataclass
class ConceptExtractionResult:
    """Results from concept extraction."""
    frameworks: List[ExtractedConcept]
    constructs: List[ExtractedConcept]
    measures: List[ExtractedConcept]
    paradigms: List[ExtractedConcept]
    relationships: List[Dict[str, str]]  # {"source": "X", "target": "Y", "type": "predicts"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "frameworks": [f.to_dict() for f in self.frameworks],
            "constructs": [c.to_dict() for c in self.constructs],
            "measures": [m.to_dict() for m in self.measures],
            "paradigms": [p.to_dict() for p in self.paradigms],
            "relationships": self.relationships,
        }


class ConceptExtractionError(Exception):
    """Raised when concept extraction fails."""
    pass


async def extract_concepts_from_papers(
    papers: List[Paper],
    max_retries: int = 3
) -> ConceptExtractionResult:
    """Extract concepts from a list of papers using Gemini.
    
    Args:
        papers: List of Paper objects with abstracts
        max_retries: Maximum retry attempts for LLM calls
        
    Returns:
        ConceptExtractionResult with extracted concepts and relationships
        
    Raises:
        ConceptExtractionError: If extraction fails after retries
    """
    config = get_config()
    
    if not LLM_AVAILABLE:
        logger.warning("LLM not available, returning empty concepts")
        return ConceptExtractionResult(
            frameworks=[], constructs=[], measures=[], paradigms=[], relationships=[]
        )
    
    if not config.is_provider_available("gemini"):
        logger.warning("Gemini not available, returning empty concepts")
        return ConceptExtractionResult(
            frameworks=[], constructs=[], measures=[], paradigms=[], relationships=[]
        )
    
    logger.info(f"Extracting concepts from {len(papers)} papers")
    
    # Batch papers for efficient processing
    batch_size = 5
    all_concepts = []
    
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(papers) + batch_size - 1)//batch_size}")
        
        for attempt in range(max_retries):
            try:
                batch_concepts = await _extract_concepts_batch(batch)
                all_concepts.extend(batch_concepts)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = config.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Concept extraction attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Concept extraction failed for batch after {max_retries} attempts")
                    # Continue with other batches
    
    # Merge and deduplicate concepts
    result = _merge_concepts(all_concepts)
    
    logger.info(
        f"Extracted {len(result.frameworks)} frameworks, "
        f"{len(result.constructs)} constructs, "
        f"{len(result.measures)} measures, "
        f"{len(result.paradigms)} paradigms"
    )
    
    return result


async def _extract_concepts_batch(papers: List[Paper]) -> List[Dict[str, Any]]:
    """Extract concepts from a batch of papers using Gemini.
    
    Args:
        papers: Batch of papers to process
        
    Returns:
        List of concept dictionaries
    """
    llm = LLMManager(ConfigurationManager())
    
    # Build prompt with paper abstracts
    papers_text = "\n\n".join([
        f"Paper {i+1}: {p.title}\nAbstract: {p.abstract}"
        for i, p in enumerate(papers)
    ])
    
    prompt = f"""Analyze these research papers and extract key concepts:

{papers_text}

For each paper, identify:
1. **Theoretical frameworks** - Major theories or models (e.g., "Attachment Theory", "Social Cognitive Theory")
2. **Constructs** - Key psychological/behavioral variables (e.g., "attachment anxiety", "emotion regulation")
3. **Measures** - Specific instruments or scales (e.g., "ECR-R", "STAI", "ERQ")
4. **Paradigms** - Experimental methods or tasks (e.g., "priming task", "daily diary study")
5. **Relationships** - How constructs relate (e.g., "attachment anxiety predicts emotion dysregulation")

Return ONLY valid JSON in this exact format:
{{
  "papers": [
    {{
      "title": "paper title",
      "frameworks": [{{"name": "Framework Name", "description": "brief description"}}],
      "constructs": [{{"name": "Construct Name", "description": "brief description"}}],
      "measures": [{{"name": "Measure/Scale Name", "description": "what it measures"}}],
      "paradigms": [{{"name": "Paradigm Name", "description": "brief description"}}],
      "relationships": [{{"source": "construct A", "target": "construct B", "type": "predicts|moderates|mediates"}}]
    }}
  ]
}}

Be specific and extract actual names from the papers. If a category is not mentioned, use empty array."""
    
    response = await llm.chat(
        [Message(role="user", content=prompt)],
        provider="gemini"
    )
    
    # Parse response (handle markdown code fences)
    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    parsed_data = json.loads(content)
    
    return parsed_data.get("papers", [])


def _merge_concepts(all_concepts: List[Dict[str, Any]]) -> ConceptExtractionResult:
    """Merge and deduplicate concepts from multiple batches.
    
    Args:
        all_concepts: List of concept dictionaries from batches
        
    Returns:
        Merged ConceptExtractionResult
    """
    # Track concepts by normalized name to deduplicate
    frameworks_dict = {}
    constructs_dict = {}
    measures_dict = {}
    paradigms_dict = {}
    all_relationships = []
    
    for paper_concepts in all_concepts:
        paper_title = paper_concepts.get("title", "Unknown")
        
        # Process frameworks
        for fw in paper_concepts.get("frameworks", []):
            name = fw["name"]
            norm_name = name.lower().strip()
            
            if norm_name not in frameworks_dict:
                frameworks_dict[norm_name] = ExtractedConcept(
                    name=name,
                    type="framework",
                    description=fw.get("description", ""),
                    papers=[paper_title],
                    frequency=1
                )
            else:
                frameworks_dict[norm_name].frequency += 1
                if paper_title not in frameworks_dict[norm_name].papers:
                    frameworks_dict[norm_name].papers.append(paper_title)
        
        # Process constructs
        for cons in paper_concepts.get("constructs", []):
            name = cons["name"]
            norm_name = name.lower().strip()
            
            if norm_name not in constructs_dict:
                constructs_dict[norm_name] = ExtractedConcept(
                    name=name,
                    type="construct",
                    description=cons.get("description", ""),
                    papers=[paper_title],
                    frequency=1
                )
            else:
                constructs_dict[norm_name].frequency += 1
                if paper_title not in constructs_dict[norm_name].papers:
                    constructs_dict[norm_name].papers.append(paper_title)
        
        # Process measures
        for meas in paper_concepts.get("measures", []):
            name = meas["name"]
            norm_name = name.lower().strip()
            
            if norm_name not in measures_dict:
                measures_dict[norm_name] = ExtractedConcept(
                    name=name,
                    type="measure",
                    description=meas.get("description", ""),
                    papers=[paper_title],
                    frequency=1
                )
            else:
                measures_dict[norm_name].frequency += 1
                if paper_title not in measures_dict[norm_name].papers:
                    measures_dict[norm_name].papers.append(paper_title)
        
        # Process paradigms
        for para in paper_concepts.get("paradigms", []):
            name = para["name"]
            norm_name = name.lower().strip()
            
            if norm_name not in paradigms_dict:
                paradigms_dict[norm_name] = ExtractedConcept(
                    name=name,
                    type="paradigm",
                    description=para.get("description", ""),
                    papers=[paper_title],
                    frequency=1
                )
            else:
                paradigms_dict[norm_name].frequency += 1
                if paper_title not in paradigms_dict[norm_name].papers:
                    paradigms_dict[norm_name].papers.append(paper_title)
        
        # Collect relationships (deduplicate by source-target-type tuple)
        for rel in paper_concepts.get("relationships", []):
            all_relationships.append(rel)
    
    # Deduplicate relationships
    unique_relationships = []
    seen_relationships = set()
    for rel in all_relationships:
        rel_tuple = (rel["source"].lower(), rel["target"].lower(), rel["type"])
        if rel_tuple not in seen_relationships:
            unique_relationships.append(rel)
            seen_relationships.add(rel_tuple)
    
    # Sort by frequency (most common first)
    frameworks = sorted(frameworks_dict.values(), key=lambda x: x.frequency, reverse=True)
    constructs = sorted(constructs_dict.values(), key=lambda x: x.frequency, reverse=True)
    measures = sorted(measures_dict.values(), key=lambda x: x.frequency, reverse=True)
    paradigms = sorted(paradigms_dict.values(), key=lambda x: x.frequency, reverse=True)
    
    return ConceptExtractionResult(
        frameworks=frameworks,
        constructs=constructs,
        measures=measures,
        paradigms=paradigms,
        relationships=unique_relationships
    )


async def extract_concepts_from_single_paper(paper: Paper) -> Dict[str, Any]:
    """Convenience function to extract concepts from a single paper.
    
    Args:
        paper: Single Paper object
        
    Returns:
        Dictionary with extracted concepts
    """
    result = await extract_concepts_from_papers([paper])
    return result.to_dict()
