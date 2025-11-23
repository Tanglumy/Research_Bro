"""Literature Explorer Module.

Extracts concepts from research questions, searches academic literature,
builds knowledge graphs, and identifies research gaps.
"""

import logging
import uuid
from typing import Dict, Any, List

from spoon_ai.llm import LLMManager
from spoon_ai.schema import Message
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    ResearchQuestion,
    Concept,
    ConceptEdge,
    KnowledgeGraph,
    LiteratureGap,
    LiteratureLandscape,
    Operationalization
)


# Import Google Scholar search (fast SerpAPI-based search)
try:
    from .google_scholar_search import search_multiple_queries
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    logging.debug("Google Scholar search not available.")

logger = logging.getLogger(__name__)


class LiteratureExplorer:
    """Explores literature landscape from research questions."""
    
    def __init__(self, llm_manager: LLMManager):
        """Initialize the Literature Explorer.
        
        Args:
            llm_manager: LLM manager for text generation
        """
        self.llm = llm_manager
        logger.info("LiteratureExplorer initialized with Google Scholar search")
    
    async def explore(self, research_question: ResearchQuestion) -> LiteratureLandscape:
        """Execute the complete literature exploration workflow.
        
        Args:
            research_question: The research question to explore
            
        Returns:
            LiteratureLandscape with knowledge graph and gaps
        """
        logger.info(f"Starting literature exploration for: {research_question.raw_text}")
        
        # Step 1: Extract and parse constructs
        constructs = await self._extract_constructs(research_question)
        research_question.parsed_constructs = constructs
        
        # Step 2: Build knowledge graph
        knowledge_graph = await self._build_knowledge_graph(constructs)
        
        # Step 3: Search and structure literature
        literature_data = await self._search_literature(constructs)
        
        # Step 4: Identify frameworks and measures
        frameworks = await self._identify_frameworks(literature_data)
        measures = await self._identify_measures(literature_data, constructs)
        paradigms = await self._identify_paradigms(literature_data)
        
        # Step 5: Identify gaps
        gaps = await self._identify_gaps(research_question, literature_data, knowledge_graph)
        
        # Step 6: Generate summary
        summary = await self._generate_summary(
            research_question,
            knowledge_graph,
            frameworks,
            measures,
            gaps
        )
        
        # Create landscape object
        landscape = LiteratureLandscape(
            research_question_id=research_question.id,
            knowledge_graph=knowledge_graph,
            theoretical_frameworks=frameworks,
            common_measures=measures,
            experimental_paradigms=paradigms,
            gaps=gaps,
            summary=summary,
            citations=literature_data.get("citations", [])
        )
        
        logger.info("Literature exploration completed")
        return landscape
    
    async def _extract_constructs(self, research_question: ResearchQuestion) -> List[str]:
        """Extract key constructs from research question.
        
        Args:
            research_question: Research question to analyze
            
        Returns:
            List of identified constructs
        """
        prompt = f"""Analyze this research question and extract the key theoretical constructs, variables, and concepts.

Research Question: {research_question.raw_text}

Provide a list of 3-7 key constructs that are central to this research question.
Focus on:
- Psychological/behavioral constructs (e.g., attachment, emotion regulation)
- Outcome variables (e.g., well-being, performance)
- Populations or contexts if specific

Return as a JSON array of strings."""
        
        response = await self.llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.3
        )
        
        # Parse constructs from response
        import json
        try:
            constructs = json.loads(response.content)
            if isinstance(constructs, dict) and "constructs" in constructs:
                constructs = constructs["constructs"]
        except json.JSONDecodeError:
            # Fallback: extract from text
            constructs = [c.strip() for c in response.content.split("\n") if c.strip() and not c.startswith("{")]
            constructs = [c.lstrip("-•*123456789. ") for c in constructs if len(c) > 2]
        
        logger.debug(f"Extracted constructs: {constructs}")
        return constructs[:7]  # Limit to 7
    
    async def _build_knowledge_graph(self, constructs: List[str]) -> KnowledgeGraph:
        """Build a knowledge graph from constructs.
        
        Args:
            constructs: List of constructs to map
            
        Returns:
            KnowledgeGraph with nodes and edges
        """
        graph = KnowledgeGraph()
        
        # Create nodes for each construct
        for construct in constructs:
            concept_id = f"concept_{uuid.uuid4().hex[:8]}"
            concept = Concept(
                id=concept_id,
                label=construct,
                type="theoretical_construct"
            )
            graph.add_node(concept)
        
        # Identify relationships between constructs
        if len(constructs) > 1:
            prompt = f"""Given these psychological/research constructs, identify the key theoretical relationships between them.

Constructs: {', '.join(constructs)}

For each relationship, specify:
- source construct
- target construct  
- relationship type (predicts, associated_with, moderates, mediates)

Return as JSON array of objects with 'source', 'target', 'relation_type' fields.
Only include well-established theoretical relationships."""
            
            response = await self.llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3
            )
            
            # Parse relationships
            import json
            try:
                # Clean response content - sometimes LLM wraps JSON in markdown
                content = response.content.strip()
                if content.startswith("```"):
                    # Remove markdown code blocks
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                    content = content.replace("```json", "").replace("```", "").strip()
                
                relationships = json.loads(content)
                if isinstance(relationships, dict) and "relationships" in relationships:
                    relationships = relationships["relationships"]
                
                # Add edges to graph
                concept_map = {c.label.lower(): c.id for c in graph.nodes.values()}
                for rel in relationships:
                    source_label = rel.get("source", "").lower()
                    target_label = rel.get("target", "").lower()
                    if source_label in concept_map and target_label in concept_map:
                        edge = ConceptEdge(
                            source=concept_map[source_label],
                            target=concept_map[target_label],
                            relation_type=rel.get("relation_type", "associated_with")
                        )
                        graph.add_edge(edge)
                logger.debug(f"Added {len(graph.edges)} relationships to knowledge graph")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Could not parse relationships from LLM response, continuing without them. Response was: {response.content[:200]}")
                # Continue without relationships - knowledge graph will have nodes but no edges
        
        return graph
    
    async def _search_literature(self, constructs: List[str]) -> Dict[str, Any]:
        """Search academic literature for constructs using Google Scholar.
        
        Args:
            constructs: List of constructs to search
            
        Returns:
            Dictionary with search results and citations
        """
        if not SEARCH_AVAILABLE:
            logger.debug("Google Scholar search not available, using mock data")
            return {"papers": [], "citations": []}
        
        # Build search queries from constructs
        search_queries = []
        
        # Individual construct searches (top 3)
        for construct in constructs[:3]:
            search_queries.append(construct)
        
        # Combination search if multiple constructs
        if len(constructs) >= 2:
            search_queries.append(f"{constructs[0]} AND {constructs[1]}")
        
        try:
            # Use the Google Scholar search
            results = await search_multiple_queries(search_queries, papers_per_query=10)
            logger.info(f"Found {len(results.get('papers', []))} papers from Google Scholar")
            return results
        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
            return {"papers": [], "citations": []}
    
    async def _identify_frameworks(self, literature_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify theoretical frameworks from literature.
        
        Args:
            literature_data: Search results
            
        Returns:
            List of framework descriptions
        """
        papers_text = "\n".join([p.get("title", "") + " " + p.get("abstract", "")[:200] 
                                  for p in literature_data.get("papers", [])[:10]])
        
        if not papers_text.strip():
            return [{"name": "General theoretical framework", "description": "Standard research approach in this domain"}]
        
        prompt = f"""Based on these research papers, identify 2-4 major theoretical frameworks that are commonly used.

Papers:
{papers_text}

For each framework, provide:
- name
- brief description (1-2 sentences)

Return as JSON array of objects with 'name' and 'description' fields."""
        
        response = await self.llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.4
        )
        
        import json
        try:
            frameworks = json.loads(response.content)
            if isinstance(frameworks, dict) and "frameworks" in frameworks:
                frameworks = frameworks["frameworks"]
            return frameworks[:4]
        except json.JSONDecodeError:
            return [{"name": "General theoretical framework", "description": "Standard research approach"}]
    
    async def _identify_measures(self, literature_data: Dict[str, Any], constructs: List[str]) -> Dict[str, List[str]]:
        """Identify common measurement instruments.
        
        Args:
            literature_data: Search results
            constructs: List of constructs
            
        Returns:
            Dictionary mapping constructs to measurement scales
        """
        measures_map = {}
        
        prompt = f"""For each of these psychological constructs, list 2-4 commonly used measurement scales or instruments.

Constructs: {', '.join(constructs)}

Return as JSON object where keys are constructs and values are arrays of scale names.
Example: {{"anxiety": ["STAI", "GAD-7"], "attachment": ["ECR-R", "AAI"]}}"""
        
        response = await self.llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.3
        )
        
        import json
        try:
            measures_map = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback
            for construct in constructs:
                measures_map[construct] = [f"{construct.title()} Scale", f"{construct.title()} Questionnaire"]
        
        return measures_map
    
    async def _identify_paradigms(self, literature_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify experimental paradigms and tasks.
        
        Args:
            literature_data: Search results
            
        Returns:
            List of paradigm descriptions
        """
        papers_text = "\n".join([p.get("title", "") + " " + p.get("abstract", "")[:200] 
                                  for p in literature_data.get("papers", [])[:10]])
        
        if not papers_text.strip():
            return [{"name": "Standard experimental design", "description": "Typical methodology in this area"}]
        
        prompt = f"""Based on these papers, identify 2-3 common experimental paradigms or tasks used in this research area.

Papers:
{papers_text}

For each paradigm, provide:
- name
- description (what participants do)

Return as JSON array of objects with 'name' and 'description' fields."""
        
        response = await self.llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.4
        )
        
        import json
        try:
            paradigms = json.loads(response.content)
            if isinstance(paradigms, dict) and "paradigms" in paradigms:
                paradigms = paradigms["paradigms"]
            return paradigms[:3]
        except json.JSONDecodeError:
            return [{"name": "Standard experimental design", "description": "Typical methodology"}]
    
    async def _identify_gaps(self, research_question: ResearchQuestion, 
                            literature_data: Dict[str, Any],
                            knowledge_graph: KnowledgeGraph) -> LiteratureGap:
        """Identify gaps in existing literature.
        
        Args:
            research_question: Original research question
            literature_data: Search results
            knowledge_graph: Constructed knowledge graph
            
        Returns:
            LiteratureGap object
        """
        constructs = research_question.parsed_constructs
        papers_summary = f"{len(literature_data.get('papers', []))} papers found"
        
        prompt = f"""Analyze the research landscape and identify key gaps.

Research Question: {research_question.raw_text}
Constructs: {', '.join(constructs)}
Literature: {papers_summary}

Identify gaps in:
1. Missing variable combinations (which constructs haven't been studied together?)
2. Unexplored populations (age groups, cultures, contexts not well studied)
3. Methodological gaps (needed approaches, designs, measures)
4. Theoretical gaps (unanswered questions, mechanisms)

Return as JSON with fields: 'description', 'missing_combinations', 'unexplored_populations', 'methodological_gaps', 'theoretical_gaps'.
Each field except 'description' should be an array of strings."""
        
        response = await self.llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.5
        )
        
        import json
        try:
            gaps_data = json.loads(response.content)
            return LiteratureGap(
                description=gaps_data.get("description", "Several research gaps identified"),
                missing_combinations=gaps_data.get("missing_combinations", []),
                unexplored_populations=gaps_data.get("unexplored_populations", []),
                methodological_gaps=gaps_data.get("methodological_gaps", []),
                theoretical_gaps=gaps_data.get("theoretical_gaps", [])
            )
        except (json.JSONDecodeError, KeyError):
            return LiteratureGap(
                description="Research gaps exist in construct combinations and populations",
                missing_combinations=[f"{constructs[0]} + {constructs[1]}"] if len(constructs) >= 2 else [],
                unexplored_populations=["Diverse cultural samples"],
                methodological_gaps=["Longitudinal designs"],
                theoretical_gaps=["Underlying mechanisms"]
            )
    
    async def _generate_summary(self, research_question: ResearchQuestion,
                               knowledge_graph: KnowledgeGraph,
                               frameworks: List[Dict[str, Any]],
                               measures: Dict[str, List[str]],
                               gaps: LiteratureGap) -> str:
        """Generate human-readable summary of literature landscape.
        
        Args:
            research_question: Original question
            knowledge_graph: Knowledge graph
            frameworks: Identified frameworks
            measures: Common measures
            gaps: Research gaps
            
        Returns:
            Formatted summary text
        """
        prompt = f"""Create a concise summary (3-4 paragraphs) of the literature landscape for this research question.

Research Question: {research_question.raw_text}

Key Constructs: {', '.join(research_question.parsed_constructs)}
Theoretical Frameworks: {', '.join([f['name'] for f in frameworks])}
Key Measures: {', '.join([f"{k}: {', '.join(v[:2])}" for k, v in list(measures.items())[:3]])}

Research Gaps:
{gaps.description}

Write a clear, informative summary that:
1. Describes the current state of research
2. Highlights key theoretical perspectives
3. Notes common methodological approaches
4. Emphasizes the identified gaps

Use professional academic tone."""
        
        summary = await self.llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.6
        )
        
        return summary.content
