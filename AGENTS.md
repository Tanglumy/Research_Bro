# AGENTS.md

This file provides guidance to agents (i.e., ADAL) when working with code in this repository.

## Project Overview

This is a research copilot system built on SpoonOS that guides researchers from fuzzy ideas to experimental designs with synthetic data validation. The system uses a graph-based workflow to orchestrate five core capability modules:

1. **Literature Landscape Explorer** - Maps research landscape, identifies gaps
2. **Hypothesis Generator & Structurer** - Generates testable hypotheses with IVs/DVs/mediators
3. **Experimental Design Builder & Critic** - Proposes designs, checks confounds, drafts Methods sections
4. **Stimulus Factory** - Generates balanced experimental stimuli with metadata
5. **Synthetic Participant Simulator** - Simulates responses to validate designs

## Architecture

### SpoonOS Core Components

The system is built on three foundational SpoonOS systems:

**1. Graph System (`spoon-core/spoon_ai/graph/`)**
- `StateGraph`: Define workflows as directed graphs of nodes (async functions) and edges
- `GraphAgent`: Execute compiled graphs with state management and checkpointing
- State is immutable: each node returns partial dict merged into shared state
- Pattern: `graph.add_node(name, async_func)` → `graph.add_edge(source, target)` → `graph.compile()`
- See `spoon-core/doc/graph_agent.md` for detailed patterns

**2. LLM System (`spoon-core/spoon_ai/llm/`)**
- `LLMManager`: Unified interface across OpenAI/Anthropic/DeepSeek/Gemini/OpenRouter
- `ConfigurationManager`: Load configs from env vars or JSON/TOML files
- Provider registration via `@register_provider` decorator
- Supports chat, streaming, tool calling, fallback chains
- Configure via env vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, etc.
- See `spoon-core/spoon_ai/llm/README.md` for provider details

**3. Toolkit System (`spoon-toolkit/spoon_toolkits/`)**
- **Data/Search**: `ResearchAcademicSearchTool`, `ResearchWebSearchTool`, `ResearchTwitterSearchTool`
- **Crypto Data**: Price data, alerts, holders, trading history, wallet analysis
- **Blockchain**: Chainbase (blocks/txns/balances), ThirdWeb Insight, Neo N3 API
- **Storage**: AIOZ, 4EVERLAND, OORT decentralized storage
- **Social**: Discord, Twitter, Telegram, Email notification tools
- **GitHub**: Issue/PR/commit analysis tools
- All tools subclass `BaseTool` with `async def execute(**kwargs)`
- See `spoon-toolkit/README.md` for per-tool env var requirements

### Research Copilot Implementation

**Module Organization:**
```
research_copilot/
  modules/
    literature_explorer.py    # Module 1
    hypothesis_generator.py   # Module 2 (to be implemented)
    design_builder.py         # Module 3 (to be implemented)
    stimulus_factory.py       # Module 4 (to be implemented)
    simulator.py              # Module 5 (to be implemented)
  models.py                   # Shared data models (ResearchQuestion, Concept, Hypothesis, etc.)
  state_service.py            # Project state persistence service
  api.py                      # API endpoints
```

**Shared Data Models** (`models.py`):
- `ResearchQuestion`: User input + parsed constructs
- `Concept`: Graph nodes with labels, types, linked papers, measures, operationalizations
- `Edge`: Graph edges with source/target/relation_type
- `Hypothesis`: IVs/DVs/mediators/moderators with theoretical basis
- `ExperimentDesign`: Design type, conditions, measures, sample size plan
- `StimulusItem`: Text + metadata (valence, relationship_type, intensity, etc.)
- `SyntheticParticipant`: Persona + simulated responses

**State Service Pattern:**
- Canonical project state with versioned checkpoints
- Exposes read/write endpoints for all object types
- Enables module composition: each module can run independently or in sequence
- State persists to graph DB (concepts/edges), document store (papers), JSON/relational store (hypotheses/designs/stimuli)

**Workflow Orchestration Pattern:**
```python
# Each module is a graph node
async def literature_node(state):
    return {"literature": await fetch_landscape(state["rq"])}

async def hypothesis_node(state):
    return {"hypotheses": await gen_hypotheses(state)}

# Wire modules into graph
graph = StateGraph()
graph.add_node("literature", literature_node)
graph.add_node("hypotheses", hypothesis_node)
graph.set_entry_point("literature")
graph.add_edge("literature", "hypotheses")

# Add conditional routing for human-in-the-loop
def route_after_hypotheses(state):
    return "approved" if state.get("user_approved") else "revise"

graph.add_conditional_edges("hypotheses", route_after_hypotheses, {
    "approved": "design",
    "revise": "hypotheses"
})

compiled = graph.compile()
agent = GraphAgent(name="research_copilot", graph=graph, initial_state={"rq": "..."})
result = await agent.run("start")
```

## Development Setup

### Environment Activation
```bash
source spoon-env/bin/activate
```

### Install Dependencies
```bash
# Core framework
pip install -r spoon-core/requirements.txt

# Toolkit (data/crypto/storage/social tools)
pip install -r spoon-toolkit/requirements.txt
```

### Environment Variables

Create `.env` file in project root with required API keys:

```bash
# LLM Providers (at least one required)
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
DEEPSEEK_API_KEY="..."

# Research/Data Tools
BITQUERY_API_KEY="..."
BITQUERY_CLIENT_ID="..."
BITQUERY_CLIENT_SECRET="..."

# Blockchain Data
CHAINBASE_API_KEY="..."
THIRDWEB_CLIENT_ID="..."

# Crypto Data (for DEX queries)
OKX_API_KEY="..."
OKX_SECRET_KEY="..."
OKX_API_PASSPHRASE="..."
OKX_PROJECT_ID="..."

# Storage Services
AIOZ_ACCESS_KEY="..."
AIOZ_SECRET_KEY="..."
FOUREVERLAND_ACCESS_KEY="..."
FOUREVERLAND_SECRET_KEY="..."
OORT_ACCESS_KEY="..."
OORT_SECRET_KEY="..."

# Social/Notifications
DISCORD_BOT_TOKEN="..."
TWITTER_API_KEY="..."
TELEGRAM_BOT_TOKEN="..."

# GitHub Analysis
GITHUB_TOKEN="ghp_..."
```

### Running the System

```bash
# Display banner (basic CLI bootstrapper)
python main.py

# Run workflow examples
python research_copilot/examples/test_workflow.py

# Run graph agent examples
python spoon-core/examples/agent/graph_agent_example.py
```

## Key Development Patterns

### Creating a New Research Module

1. **Define the Node Function** in `research_copilot/modules/`:
```python
async def new_module_node(state: dict) -> dict:
    # Extract inputs from state
    input_data = state.get("previous_module_output")
    
    # Use LLM for generation
    llm = LLMManager(ConfigurationManager())
    response = await llm.chat(messages=[{"role": "user", "content": prompt}], provider="openai")
    
    # Use toolkit for data retrieval
    from spoon_toolkits.data_platforms.Research import ResearchAcademicSearchTool
    search_tool = ResearchAcademicSearchTool()
    papers = await search_tool.execute(query="...", limit=10)
    
    # Return state updates
    return {"new_module_output": result}
```

2. **Add to Workflow Graph** in orchestrator:
```python
graph.add_node("new_module", new_module_node)
graph.add_edge("previous_module", "new_module")
```

3. **Update State Service** to persist new data types

4. **Add Data Model** to `models.py` if needed

### Using LLM System

```python
from spoon_ai.llm import LLMManager, ConfigurationManager

llm = LLMManager(ConfigurationManager())  # Reads from env vars

# Simple chat
response = await llm.chat(
    messages=[{"role": "user", "content": "Summarize literature gaps"}],
    provider="anthropic"  # or "openai", "deepseek"
)

# Chat with tools
tools = [{
    "name": "search_academic",
    "description": "Search academic papers",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}
}]
response = await llm.chat_with_tools(messages=[...], tools=tools, provider="openai")

# Streaming
async for chunk in llm.chat_stream(messages=[...], provider="anthropic"):
    print(chunk, end="")
```

### Using Toolkit

```python
# Academic search
from spoon_toolkits.data_platforms.Research import ResearchAcademicSearchTool
tool = ResearchAcademicSearchTool()
results = await tool.execute(query="emotion regulation attachment", limit=10)

# Web search
from spoon_toolkits.data_platforms.Research import ResearchWebSearchTool
tool = ResearchWebSearchTool()
results = await tool.execute(query="experimental design best practices")

# Blockchain data
from spoon_toolkits.chainbase import GetAccountBalanceTool
tool = GetAccountBalanceTool()
balance = await tool.execute(chain_id=1, address="0x...")

# Storage
from spoon_toolkits.storage.aioz.aioz_tools import AiozStorageTool
tool = AiozStorageTool()
result = await tool.upload_file(bucket_name="research-data", file_path="./stimuli.json")
```

### Graph State Management

```python
# State is immutable - return partial updates
async def node_function(state: dict) -> dict:
    # Read from state
    previous_result = state.get("previous_step")
    
    # Never modify state directly
    # state["new_key"] = value  # DON'T DO THIS
    
    # Return updates to merge
    return {
        "new_key": computed_value,
        "updated_key": modified_value
    }

# Conditional routing based on state
def route_function(state: dict) -> str:
    if state.get("needs_revision"):
        return "revise"
    elif state.get("user_approved"):
        return "continue"
    return "end"

graph.add_conditional_edges("check_node", route_function, {
    "revise": "previous_node",
    "continue": "next_node",
    "end": END
})
```

## Testing and Debugging

### Enable Debug Logging
```python
import logging
from spoon_ai.llm import get_debug_logger

logging.basicConfig(level=logging.DEBUG)
debug_logger = get_debug_logger()
debug_logger.set_log_level("DEBUG")
debug_logger.enable_request_logging()
```

### Monitor LLM Performance
```python
from spoon_ai.llm import get_metrics_collector

metrics = get_metrics_collector()
stats = metrics.get_provider_stats("openai")
print(f"Success rate: {stats.successful_requests / stats.total_requests * 100:.1f}%")
print(f"Average response time: {stats.avg_response_time:.2f}s")
```

### Check Provider Health
```python
health_status = await llm_manager.health_check_all()
for provider, is_healthy in health_status.items():
    status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
    print(f"{provider}: {status}")
```

### Graph Execution History
```python
agent = GraphAgent(name="test", graph=graph)
result = await agent.run("start")

# Inspect execution path
for step in agent.get_execution_history():
    print(f"Node: {step['node']}, Duration: {step['duration']}s")
```

## Common Development Tasks

### Adding a New LLM Provider

1. For OpenAI-compatible APIs:
```python
from spoon_ai.llm.providers.openai_compatible_provider import OpenAICompatibleProvider
from spoon_ai.llm import register_provider, ProviderCapability

@register_provider("custom_provider", [ProviderCapability.CHAT])
class CustomProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__()
        self.provider_name = "custom_provider"
        self.default_base_url = "https://api.custom.com/v1"
        self.default_model = "custom-model"
```

2. For non-OpenAI APIs, implement `LLMProviderInterface`

### Adding a New Tool to Toolkit

1. Create tool class in appropriate `spoon-toolkit/spoon_toolkits/` subdirectory
2. Subclass `BaseTool` and implement `async def execute(**kwargs)`
3. Add required env vars to `spoon-toolkit/README.md`
4. Import in `__init__.py` for easy access

### Persisting Research Project State

1. Define data model in `research_copilot/models.py`
2. Add serialization/deserialization methods
3. Update `state_service.py` with read/write endpoints
4. Use state service in graph nodes to persist/retrieve data

## Coding Standards

- Python 3.11+; follow PEP 8 (4-space indent, snake_case for functions/vars, PascalCase for classes)
- Keep modules cohesive: core framework code in `spoon_core`, toolkit additions in `spoon_toolkits`
- Add short, meaningful docstrings and type hints
- Configuration: prefer environment variables (`.env`) over hardcoded secrets; never commit keys
- Tests: When adding behavior, create focused tests under `spoon-core/tests/` mirroring module paths
- Name tests `test_<module>.py`; prefer pytest-style asserts

## File Organization

- **SpoonOS Core** (`spoon-core/spoon_ai/`): Framework code - graph system, LLM manager, base agents
- **Toolkit** (`spoon-toolkit/spoon_toolkits/`): Reusable tools - data/crypto/storage/social
- **Research Copilot** (`research_copilot/`): Application logic - modules, models, state service, API
- **Examples** (`spoon-core/examples/`, `research_copilot/examples/`): Reference implementations
- **Documentation** (`spoon-core/doc/`, `*.md`): Architecture and API docs

## Important Notes

### SpoonOS Workflow Philosophy
- Each capability module is a graph node (async function)
- State flows through nodes and accumulates results
- Use conditional edges for branching (human approval, validation, error handling)
- Checkpoints enable resume/replay for long-running workflows
- Project state service provides canonical storage for cross-module data

### Configuration Management
- Environment variables take precedence over config files
- Use `ConfigurationManager` for consistent config loading
- Provider-specific settings: `<PROVIDER>_API_KEY`, `<PROVIDER>_MODEL`, etc.
- Toolkit tools require different env vars - check `spoon-toolkit/README.md`

### Error Handling
- LLM system has standardized error hierarchy: `LLMError`, `ProviderError`, `RateLimitError`, `AuthenticationError`
- Use fallback chains for resilience: `llm_manager.set_fallback_chain(["openai", "anthropic", "deepseek"])`
- Graph nodes should return error states rather than raising exceptions to allow conditional recovery

### Performance Considerations
- Use streaming for long LLM responses: `llm.chat_stream()`
- Enable connection pooling for repeated API calls
- Cache expensive operations (literature search results, concept graphs)
- Use background tasks for non-blocking operations
