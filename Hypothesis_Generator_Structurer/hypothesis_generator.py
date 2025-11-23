#!/usr/bin/env python3
"""Hypothesis Generator: Generate structured hypotheses from literature knowledge graph.

This module uses OpenAI to:
1. Analyze concepts and relationships from Module 1's knowledge graph
2. Identify potential IV/DV combinations
3. Propose mediators and moderators
4. Generate 3-5 testable hypotheses with theoretical grounding
"""

import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths
root = Path(__file__).resolve().parent.parent
for p in [root / "spoon-core", root / "spoon-toolkit", root]:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

try:
    from spoon_ai.llm import LLMManager, ConfigurationManager
    from spoon_ai.schema import Message
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("LLM tools not available. Hypothesis generation will be limited.")

from copilot_workflow.config import get_config
from copilot_workflow.schemas import Hypothesis, ProjectState

logger = logging.getLogger(__name__)


class HypothesisGenerationError(Exception):
    """Raised when hypothesis generation fails."""
    pass


@dataclass
class HypothesisGenerationResult:
    """Result of hypothesis generation."""
    hypotheses: List[Hypothesis]
    summary: str
    raw_analysis: str


async def generate_hypotheses(
    project: ProjectState,
    num_hypotheses: int = 5,
    max_retries: Optional[int] = None
) -> HypothesisGenerationResult:
    """Generate structured hypotheses from knowledge graph.
    
    Uses OpenAI to analyze:
    - Research question constructs
    - Concept nodes and edges from literature
    - Gap analysis results
    
    Produces:
    - 3-5 testable hypotheses
    - Each with IV, DV, mediators, moderators
    - Theoretical justification
    - Expected direction
    
    Args:
        project: ProjectState with RQ and concepts from Module 1
        num_hypotheses: Target number of hypotheses (default: 5)
        max_retries: Override default retry count
        
    Returns:
        HypothesisGenerationResult with list of Hypothesis objects
        
    Raises:
        HypothesisGenerationError: If generation fails after retries
    """
    try:
        config = get_config()
    except Exception as exc:  # pragma: no cover - defensive in tests
        logger.warning(f"Config unavailable, using heuristic hypotheses: {exc}")
        return _generate_heuristic_result(project, num_hypotheses)
    
    # Validate inputs
    if not project.rq:
        raise HypothesisGenerationError("Research question missing")
    
    if not project.rq.parsed_constructs:
        raise HypothesisGenerationError("No constructs parsed from research question")
    
    nodes = project.concepts.get("nodes", [])
    edges = project.concepts.get("edges", [])
    
    if not nodes:
        logger.warning("No concept nodes found - will generate hypotheses from RQ only")
    
    logger.info(f"Generating {num_hypotheses} hypotheses from {len(nodes)} concepts")
    
    # Get retry configuration
    retry_config = config.get_retry_config()
    max_retries = max_retries or retry_config["max_retries"]
    retry_delay = retry_config["retry_delay"]
    
    if _should_use_stub_mode() or not LLM_AVAILABLE or not config.is_provider_available("openai"):
        logger.info("Using heuristic hypothesis generation (LLM unavailable or offline mode)")
        return _generate_heuristic_result(project, num_hypotheses)
    
    # Attempt generation with retries
    for attempt in range(max_retries):
        try:
            result = await _generate_with_openai(
                project=project,
                num_hypotheses=num_hypotheses
            )
            logger.info(f"Successfully generated {len(result.hypotheses)} hypotheses")
            return result
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(
                    f"Hypothesis generation attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Hypothesis generation failed after {max_retries} attempts: {e}")
                return _generate_heuristic_result(project, num_hypotheses)
    
    logger.warning("Hypothesis generation failed after retries, using heuristic fallback")
    return _generate_heuristic_result(project, num_hypotheses)


async def _generate_with_openai(
    project: ProjectState,
    num_hypotheses: int
) -> HypothesisGenerationResult:
    """Internal function to generate hypotheses using OpenAI.
    
    Args:
        project: ProjectState with RQ and concepts
        num_hypotheses: Target number of hypotheses
        
    Returns:
        HypothesisGenerationResult
    """
    if not LLM_AVAILABLE:
        raise HypothesisGenerationError("LLM tools not available. Check SpoonOS installation.")
    
    config = get_config()
    
    # Check OpenAI availability (using gpt-4o-mini)
    if not config.is_provider_available("openai"):
        raise HypothesisGenerationError("OpenAI not available. Check OPENAI_API_KEY in .env")
    
    # Initialize LLM manager using SpoonOS infrastructure
    config_manager = ConfigurationManager()
    llm_manager = LLMManager(config_manager)
    
    # Build prompt
    prompt = _build_hypothesis_prompt(project, num_hypotheses)
    
    logger.debug(f"Sending hypothesis generation prompt to OpenAI ({len(prompt)} chars)")
    
    # Generate hypotheses using SpoonOS LLM manager with OpenAI
    messages = [Message(role="user", content=prompt)]
    response = await llm_manager.chat(
        messages,
        provider="openai"
    )
    
    raw_text = response.content
    
    logger.debug(f"Received OpenAI response ({len(raw_text)} chars)")
    
    # Parse response
    hypotheses, summary = _parse_openai_response(raw_text, project)
    
    logger.info(f"Parsed {len(hypotheses)} hypotheses from OpenAI response")
    
    return HypothesisGenerationResult(
        hypotheses=hypotheses,
        summary=summary,
        raw_analysis=raw_text
    )


def _generate_heuristic_result(
    project: ProjectState,
    num_hypotheses: int
) -> HypothesisGenerationResult:
    """Generate simple hypotheses without calling an LLM."""
    constructs: List[str] = list(project.rq.parsed_constructs or [])
    
    # Supplement constructs with concept node labels if available
    concept_nodes = project.concepts.get("nodes", [])
    for node in concept_nodes:
        label = getattr(node, "label", None) or str(node)
        if label and label not in constructs:
            constructs.append(label)
    
    if not constructs:
        constructs = ["independent variable", "outcome"]
    
    pairs: List[tuple[str, str]] = []
    for idx, iv in enumerate(constructs):
        for jdx, dv in enumerate(constructs):
            if idx != jdx:
                pairs.append((iv, dv))
    
    if not pairs:
        pairs = [(constructs[0], "outcome")]
    
    selected_pairs = pairs[: max(1, num_hypotheses)]
    hypotheses: List[Hypothesis] = []
    
    for i, (iv, dv) in enumerate(selected_pairs, 1):
        mediators = constructs[2:3] if len(constructs) > 2 else []
        moderators = constructs[3:4] if len(constructs) > 3 else []
        hypothesis_text = (
            f"{iv.title()} will positively influence {dv} compared to baseline conditions."
        )
        hypotheses.append(
            Hypothesis(
                id=f"heuristic_{i}",
                text=hypothesis_text,
                iv=[iv],
                dv=[dv],
                mediators=mediators,
                moderators=moderators,
                theoretical_basis=[f"Literature on {iv}", f"Findings on {dv}"],
                expected_direction="positive"
            )
        )
    
    summary = (
        f"Heuristic generator produced {len(hypotheses)} hypotheses "
        f"using {len(constructs)} constructs."
    )
    
    return HypothesisGenerationResult(
        hypotheses=hypotheses,
        summary=summary,
        raw_analysis=summary
    )


def _should_use_stub_mode() -> bool:
    """Detect offline/test runs to avoid network calls."""
    flag = os.getenv("OFFLINE_MODE", "").lower()
    return flag in {"1", "true", "yes"} or bool(os.getenv("PYTEST_CURRENT_TEST"))

def _build_hypothesis_prompt(project: ProjectState, num_hypotheses: int) -> str:
    """Build prompt for OpenAI hypothesis generation.
    
    Args:
        project: ProjectState with RQ and concepts
        num_hypotheses: Target number of hypotheses
        
    Returns:
        Prompt string
    """
    rq = project.rq
    nodes = project.concepts.get("nodes", [])
    edges = project.concepts.get("edges", [])
    
    # Format concept graph summary
    graph_summary = _format_graph_summary(nodes, edges)
    
    prompt = f"""You are a research methodology expert. Generate {num_hypotheses} structured, testable hypotheses based on the research question and literature knowledge graph.

**RESEARCH QUESTION:**
{rq.raw_text}

**PARSED CONSTRUCTS:**
{', '.join(rq.parsed_constructs)}

**DOMAIN:**
{rq.domain or 'Not specified'}

**KNOWLEDGE GRAPH FROM LITERATURE:**
{graph_summary}

**TASK:**
Generate {num_hypotheses} structured hypotheses that:
1. Are testable through empirical research
2. Clearly specify IV (independent variable) and DV (dependent variable)
3. Include mediators or moderators where theoretically justified
4. Are grounded in the theoretical frameworks from the literature
5. Represent diverse approaches (direct effects, mediation, moderation)
6. Cover different aspects of the research question

**OUTPUT FORMAT:**
Respond with ONLY a JSON code block (```json ... ```) containing:

```json
{{
  "hypotheses": [
    {{
      "text": "Plain English hypothesis statement",
      "iv": ["Independent variable(s)"],
      "dv": ["Dependent variable(s)"],
      "mediators": ["Mediating variable(s) if applicable"],
      "moderators": ["Moderating variable(s) if applicable"],
      "theoretical_basis": ["Theoretical framework 1", "Theoretical framework 2"],
      "expected_direction": "Expected direction of effect (e.g., 'Higher IV predicts lower DV')"
    }}
  ],
  "summary": "Brief summary of the hypothesis generation approach and key themes"
}}
```

**EXAMPLE HYPOTHESIS:**
```json
{{
  "text": "Higher attachment anxiety predicts greater use of maladaptive emotion regulation strategies in romantic conflict situations",
  "iv": ["Attachment anxiety"],
  "dv": ["Emotion regulation strategy use"],
  "mediators": [],
  "moderators": [],
  "theoretical_basis": ["Attachment Theory", "Emotion Regulation Framework"],
  "expected_direction": "Higher attachment anxiety → More maladaptive strategies (positive correlation)"
}}
```

**CRITICAL REQUIREMENTS:**
- Each hypothesis MUST have at least one IV and one DV
- Mediators/moderators should only be included when theoretically justified
- All variables should be operationalizable (measurable or manipulable)
- Theoretical basis should reference frameworks from the knowledge graph
- Respond ONLY with the JSON code block, no additional text
"""
    
    return prompt


def _format_graph_summary(nodes: List[Any], edges: List[Any]) -> str:
    """Format knowledge graph for prompt.
    
    Args:
        nodes: List of ConceptNode objects (or dicts)
        edges: List of ConceptEdge objects (or dicts)
        
    Returns:
        Human-readable graph summary
    """
    if not nodes:
        return "No concept nodes available (generating from research question only)"
    
    summary_parts = []
    
    # Format nodes
    summary_parts.append(f"**CONCEPTS ({len(nodes)} total):**")
    for i, node in enumerate(nodes[:15]):  # Limit to top 15 to save tokens
        if isinstance(node, dict):
            label = node.get("label", "Unknown")
            node_type = node.get("type", "Unknown")
            measures = node.get("common_measures", [])
        else:
            label = node.label
            node_type = node.type
            measures = node.common_measures
        
        measures_str = ", ".join(measures[:3]) if measures else "No measures"
        summary_parts.append(f"  {i+1}. {label} (Type: {node_type}, Measures: {measures_str})")
    
    if len(nodes) > 15:
        summary_parts.append(f"  ... and {len(nodes) - 15} more concepts")
    
    # Format edges
    if edges:
        summary_parts.append(f"\n**RELATIONSHIPS ({len(edges)} total):**")
        for i, edge in enumerate(edges[:10]):  # Limit to top 10
            if isinstance(edge, dict):
                source = edge.get("source", "?")
                target = edge.get("target", "?")
                relation = edge.get("relation_type", "related_to")
            else:
                source = edge.source
                target = edge.target
                relation = edge.relation_type
            
            summary_parts.append(f"  {i+1}. {source} --[{relation}]--> {target}")
        
        if len(edges) > 10:
            summary_parts.append(f"  ... and {len(edges) - 10} more relationships")
    else:
        summary_parts.append("\n**RELATIONSHIPS:** None identified")
    
    return "\n".join(summary_parts)


def _parse_openai_response(raw_text: str, project: ProjectState) -> tuple[List[Hypothesis], str]:
    """Parse OpenAI response into Hypothesis objects.
    
    Handles JSON markdown fences (```json ... ```) that LLMs commonly use.
    
    Args:
        raw_text: Raw response from OpenAI
        project: ProjectState for context
        
    Returns:
        Tuple of (list of Hypothesis objects, summary string)
        
    Raises:
        HypothesisGenerationError: If parsing fails
    """
    # Extract JSON from markdown fence
    json_match = re.search(r'```json\s*\n(.*?)\n```', raw_text, re.DOTALL)
    if not json_match:
        raise HypothesisGenerationError(
            "Could not find JSON code block in OpenAI response. "
            f"Response: {raw_text[:200]}..."
        )
    
    json_str = json_match.group(1)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise HypothesisGenerationError(f"Failed to parse JSON: {e}. JSON: {json_str[:200]}...")
    
    # Extract hypotheses array
    hypotheses_data = data.get("hypotheses", [])
    if not hypotheses_data:
        raise HypothesisGenerationError("No hypotheses found in response")
    
    # Parse into Hypothesis objects
    hypotheses = []
    for i, hyp_data in enumerate(hypotheses_data):
        try:
            hypothesis = Hypothesis(
                text=hyp_data.get("text", ""),
                iv=hyp_data.get("iv", []),
                dv=hyp_data.get("dv", []),
                mediators=hyp_data.get("mediators", []),
                moderators=hyp_data.get("moderators", []),
                theoretical_basis=hyp_data.get("theoretical_basis", []),
                expected_direction=hyp_data.get("expected_direction")
            )
            hypotheses.append(hypothesis)
            logger.debug(f"Parsed hypothesis {i+1}: {hypothesis.text[:60]}...")
            
        except Exception as e:
            logger.warning(f"Failed to parse hypothesis {i+1}: {e}. Data: {hyp_data}")
            continue
    
    if not hypotheses:
        raise HypothesisGenerationError("No valid hypotheses could be parsed")
    
    # Extract summary
    summary = data.get("summary", "No summary provided")
    
    return hypotheses, summary
