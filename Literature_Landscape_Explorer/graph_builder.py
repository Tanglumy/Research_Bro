"""Build knowledge graph from extracted concepts.

Converts extracted concepts into ConceptNode and ConceptEdge objects
compatible with the project schema.
"""

import logging
from typing import List, Dict, Any
from dataclasses import asdict

try:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.append(str(root))
    
    from copilot_workflow.schemas import ConceptNode, ConceptEdge
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    logging.warning("Schema not available for graph building")

from Literature_Landscape_Explorer.concept_extraction import ConceptExtractionResult, ExtractedConcept
from Literature_Landscape_Explorer.paper_retrieval import Paper

logger = logging.getLogger(__name__)


def build_knowledge_graph(
    extraction_result: ConceptExtractionResult,
    papers: List[Paper]
) -> Dict[str, List]:
    """Build knowledge graph from extracted concepts.
    
    Converts extracted concepts into ConceptNode and ConceptEdge objects
    that are compatible with the project schema.
    
    Args:
        extraction_result: Result from concept extraction
        papers: Original papers used for extraction
        
    Returns:
        Dictionary with 'nodes' and 'edges' lists
    """
    if not SCHEMA_AVAILABLE:
        logger.warning("Schema not available, returning empty graph")
        return {"nodes": [], "edges": []}
    
    nodes = []
    edges = []
    
    # Track which papers link to which concepts
    paper_lookup = {p.title: p for p in papers}
    
    # Create nodes for theoretical frameworks
    for framework in extraction_result.frameworks:
        node = _create_concept_node(
            concept=framework,
            concept_type="theoretical_framework",
            papers=papers
        )
        nodes.append(node)
    
    # Create nodes for constructs
    for construct in extraction_result.constructs:
        node = _create_concept_node(
            concept=construct,
            concept_type="theoretical_construct",
            papers=papers
        )
        nodes.append(node)
    
    # Create nodes for measures
    for measure in extraction_result.measures:
        node = _create_concept_node(
            concept=measure,
            concept_type="measurement_instrument",
            papers=papers
        )
        nodes.append(node)
    
    # Create nodes for paradigms
    for paradigm in extraction_result.paradigms:
        node = _create_concept_node(
            concept=paradigm,
            concept_type="experimental_paradigm",
            papers=papers
        )
        nodes.append(node)
    
    # Create edges from relationships
    for rel in extraction_result.relationships:
        edge = ConceptEdge(
            source=rel["source"],
            target=rel["target"],
            relation_type=rel["type"]
        )
        edges.append(edge)
    
    # Add edges between measures and constructs (measures operationalize constructs)
    for measure in extraction_result.measures:
        # Find constructs mentioned in same papers
        for construct in extraction_result.constructs:
            if _shares_papers(measure, construct):
                edge = ConceptEdge(
                    source=measure.name,
                    target=construct.name,
                    relation_type="operationalizes"
                )
                edges.append(edge)
    
    # Add edges between paradigms and constructs
    for paradigm in extraction_result.paradigms:
        for construct in extraction_result.constructs:
            if _shares_papers(paradigm, construct):
                edge = ConceptEdge(
                    source=paradigm.name,
                    target=construct.name,
                    relation_type="investigates"
                )
                edges.append(edge)
    
    # Add edges between frameworks and constructs
    for framework in extraction_result.frameworks:
        for construct in extraction_result.constructs:
            if _shares_papers(framework, construct):
                edge = ConceptEdge(
                    source=framework.name,
                    target=construct.name,
                    relation_type="explains"
                )
                edges.append(edge)
    
    logger.info(f"Built knowledge graph with {len(nodes)} nodes and {len(edges)} edges")
    
    return {"nodes": nodes, "edges": edges}


def _create_concept_node(
    concept: ExtractedConcept,
    concept_type: str,
    papers: List[Paper]
) -> ConceptNode:
    """Create a ConceptNode from an ExtractedConcept.
    
    Args:
        concept: Extracted concept
        concept_type: Type of concept node
        papers: All papers for lookup
        
    Returns:
        ConceptNode object
    """
    # Generate unique ID from concept name
    concept_id = f"concept_{hash(concept.name) % 1000000}"
    
    # Find paper IDs (use titles as proxies)
    linked_papers = concept.papers[:10]  # Limit to first 10 papers
    
    # Extract operationalizations for constructs
    operationalizations = []
    if concept.type == "construct":
        # Look for related measures
        operationalizations.append({
            "description": concept.description,
            "typical_DVs": []  # Will be filled by gap analysis
        })
    
    # Create common measures list for constructs
    common_measures = []
    if concept.type == "construct":
        # This will be populated when we find measure relationships
        common_measures = []  # Will be filled when linking measures
    
    node = ConceptNode(
        id=concept_id,
        label=concept.name,
        type=concept_type,
        linked_papers=linked_papers,
        common_measures=common_measures,
        operationalizations=operationalizations
    )
    
    return node


def _shares_papers(concept1: ExtractedConcept, concept2: ExtractedConcept) -> bool:
    """Check if two concepts are mentioned in the same papers.
    
    Args:
        concept1: First concept
        concept2: Second concept
        
    Returns:
        True if they share at least one paper
    """
    papers1 = set(concept1.papers)
    papers2 = set(concept2.papers)
    return len(papers1 & papers2) > 0


def enrich_graph_with_measures(
    graph: Dict[str, List],
    extraction_result: ConceptExtractionResult
) -> Dict[str, List]:
    """Enrich graph nodes with measure information.
    
    Updates construct nodes with their common measures based on
    relationships in the graph.
    
    Args:
        graph: Knowledge graph with nodes and edges
        extraction_result: Extraction results with measures
        
    Returns:
        Updated graph dictionary
    """
    # Build map of construct name to node
    construct_nodes = {}
    for node in graph["nodes"]:
        if node.type == "theoretical_construct":
            construct_nodes[node.label.lower()] = node
    
    # Find measure -> construct edges
    for edge in graph["edges"]:
        if edge.relation_type == "operationalizes":
            measure_name = edge.source
            construct_name = edge.target.lower()
            
            if construct_name in construct_nodes:
                node = construct_nodes[construct_name]
                if measure_name not in node.common_measures:
                    node.common_measures.append(measure_name)
    
    return graph


def graph_to_dict(graph: Dict[str, List]) -> Dict[str, Any]:
    """Convert graph with Pydantic objects to plain dictionaries.
    
    Args:
        graph: Graph with ConceptNode and ConceptEdge objects
        
    Returns:
        Dictionary with serializable data
    """
    return {
        "nodes": [asdict(node) if hasattr(node, '__dict__') else node for node in graph["nodes"]],
        "edges": [asdict(edge) if hasattr(edge, '__dict__') else edge for edge in graph["edges"]]
    }
