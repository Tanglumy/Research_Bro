# Research Copilot on SpoonOS

Quick instructions for implementing the end-to-end research-copilot workflow on SpoonOS.

## What this does
- Takes a raw research idea → literature landscape → hypotheses → experimental design → stimuli → synthetic participants, all coordinated by SpoonOS tasks.
- Shared project state is persisted (research questions, concept graph, hypotheses, designs, stimuli, simulations) so each module can run independently or in sequence.

## Setup
- Ensure SpoonOS toolchain is available and activate the provided environment: `source spoon-env/bin/activate` (adjust if your shell uses a different activation script).
- Configure backing stores: graph DB for concepts/edges, document store for papers/abstracts, and JSON/relational store for hypotheses/designs/stimuli/simulation outputs.
- Define schemas for the shared objects (ResearchQuestion, Concept, Edge, Hypothesis, ExperimentDesign, StimulusItem, SyntheticParticipant) and register validators so tasks can trust inputs.

## SpoonOS workflow wiring
1) **Project state service**: a SpoonOS service that owns the canonical project snapshot and exposes read/write endpoints for all object types; supports versioned checkpoints for rollback and branching.
2) **Module tasks (SpoonOS services)**:
   - Literature Explorer → construct extraction, concept graph enrichment, gaps, citations.
   - Hypothesis Engine → IV/DV/mediator/moderator sets, directions, theory links; table + JSON.
   - Design Engine → design type, conditions, measures/timepoints, confound checks, N ranges, Methods draft.
   - Stimulus Engine → generates/balances stimuli with metadata, filters, and optional translations.
   - Simulation Engine → persona templates, condition assignment, DV simulations, diagnostics (dead vars/weak manipulations).
3) **Orchestrator**: a SpoonOS workflow that calls tasks in order, caches outputs in project state, and allows parallel branches (e.g., multiple hypothesis sets → multiple designs). Include resume/replay hooks and audit logs.

## Using the workflow (happy path)
1. Create/select project and store the ResearchQuestion (raw text + parsed constructs).
2. Run Literature Explorer task → updates concept graph and gap summary.
3. Pick concepts/frameworks; run Hypothesis Engine → structured hypotheses saved to state.
4. Select hypotheses; run Design Engine → design matrix + Methods draft saved to state.
5. Configure stimulus parameters; run Stimulus Engine → balanced stimulus bank with metadata.
6. Define persona mix/sample size; run Simulation Engine → synthetic data + diagnostics.
7. Export bundle (graph slice + citations, hypothesis/design tables, Methods draft, stimuli, simulation summaries) from the project state service.

## Notes
- Keep module I/O contracts explicit (JSON schemas) so tasks remain composable.
- Prefer deterministic settings for replayability; log prompts/params alongside outputs.
- Frontend can call SpoonOS endpoints to drive chat + graph panel + tables without duplicating logic.

## Spoon Toolkit API quick reference
- Install/activate: `pip install -r spoon-toolkit/requirements.txt` inside `spoon-env` so the `spoon_toolkits` package is importable. Most tools subclass `spoon_ai.tools.base.BaseTool` and expose `async def execute(**kwargs)`.
- Data/search (useful for literature + web retrieval):
  - `ResearchAISearchTool`, `ResearchAcademicSearchTool`, `ResearchWebSearchTool`, `ResearchTwitterSearchTool` (from `spoon_toolkits.data_platforms.Research`) and helpers `search_ai_data`, `search_social_media`, `search_academic`.
  - Chainbase tools (from `data_platforms.chainbase`) for on-chain blocks/transactions/balances; require `CHAINBASE_API_KEY`.
  - Thirdweb Insight tools (from `data_platforms.third_web`) for contract events, transfers, transactions, blocks, wallet history.
- Crypto data/analytics:
  - `crypto_data_tools`: price (`GetTokenPriceTool`, `Get24hStatsTool`, `GetKlineDataTool`), alerts (`PriceThresholdAlertTool`, `SuddenPriceIncreaseTool`, `LpRangeCheckTool`), holders, trading history, Uniswap liquidity, lending rates, wallet analysis, price prediction.
  - `crypto_powerdata`: `CryptoPowerDataCEXTool`, `CryptoPowerDataDEXTool`, `CryptoPowerDataIndicatorsTool`, `CryptoPowerDataPriceTool` plus MCP servers (`start_crypto_powerdata_mcp_stdio/sse/auto`) and `CryptoPowerDataMCPServer`.
- L1/L2 interaction:
  - `crypto.evm`: `EvmTransferTool`, `EvmErc20TransferTool`, `EvmSwapTool`, `EvmSwapQuoteTool`, `EvmBridgeTool`, `EvmBalanceTool`.
  - `crypto.solana`: wallet generation, transfers, SPL token ops, swaps (see `transfer.py`, `swap.py`).
  - `crypto.neo`: rich `Get…Tool` set for addresses, assets, blocks, contracts, transactions, votes, NEP11/17 transfers, SC calls; provider via `NeoProvider`.
- Storage:
  - `AiozStorageTool`, `FoureverlandStorageTool`, `OortStorageTool` (under `storage/`) for decentralized object storage; share `BaseStorageTool` interface.
- Social/notifications:
  - `DiscordTool`, `TwitterTool`, `TelegramTool`, `EmailTool` (under `social_media/`); async `send_message` helpers plus bot runners for Discord/Telegram.
- GitHub analysis:
  - `GetGitHubIssuesTool`, `GetGitHubPullRequestsTool`, `GetGitHubCommitsTool` with `GitHubProvider` for auth.
- Usage pattern:
  ```python
  from spoon_toolkits.data_platforms.Research import ResearchAcademicSearchTool
  tool = ResearchAcademicSearchTool()
  results = await tool.execute(query="emotion regulation attachment", limit=10)
  ```
  Configure required env vars per module (see `spoon-toolkit/README.md`): Bitquery/OKX/Chainbase keys, social tokens, storage creds, GitHub token, etc.

Use these tools inside SpoonOS tasks to fetch signals (search/chain data), notify users (social/email), and persist assets (storage) as part of the research-copilot flow. 

## SpoonOS LLM system quick reference
- API surface (see `spoon-core/spoon_ai/llm/README.md`): use `LLMManager` with `ConfigurationManager` to normalize provider configs and handle fallback/load-balancing.
- Basic calls:
  ```python
  from spoon_ai.llm import LLMManager, ConfigurationManager
  llm = LLMManager(ConfigurationManager())
  resp = await llm.chat([{"role": "user", "content": "Summarize the gap in emotion regulation research."}], provider="openai")
  tools = [{"name": "search_academic", "description": "Academic search"}]
  resp = await llm.chat_with_tools(messages=[{"role": "user", "content": "Find measures for attachment anxiety."}], tools=tools, provider="anthropic")
  ```
- Provider config: set env vars or `config.json` keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`; override model/temperature/max_tokens). Configure fallback chain in `llm_settings.fallback_chain` to survive outages.
- Custom providers: implement `LLMProviderInterface` or subclass `OpenAICompatibleProvider`, then `@register_provider("name", [...])`. Useful if adding in-house models for hypothesis generation or stimulus style transfer.
- Monitoring/debug: `get_debug_logger()` and `get_metrics_collector()` provide per-request logging/metrics; enable `llm_settings.enable_debug_logging` for verbose traces during workflow debugging.

## Graph system quick reference
- API surface (see `spoon-core/doc/graph_agent.md`): define a `StateGraph` with nodes (async functions returning state updates) and edges (unconditional or conditional); run via `GraphAgent`.
- Minimal pattern:
  ```python
  from spoon_ai.graph import StateGraph
  from spoon_ai.agents.graph_agent import GraphAgent

  async def literature_node(state): return {"literature": await fetch_landscape(state["rq"])}
  async def hypothesis_node(state): return {"hypotheses": await gen_hypotheses(state)}
  async def design_node(state): return {"design": await build_design(state)}

  graph = StateGraph()
  graph.add_node("literature", literature_node)
  graph.add_node("hypotheses", hypothesis_node)
  graph.add_node("design", design_node)
  graph.set_entry_point("literature")
  graph.add_edge("literature", "hypotheses")
  graph.add_edge("hypotheses", "design")
  compiled = graph.compile()

  agent = GraphAgent(name="research_copilot", graph=graph, initial_state={"rq": "attachment anxiety and emotion regulation"})
  result = await agent.run("start")  # returns merged state including design
  ```
- State rules: treat state as immutable; each node returns a partial dict merged into the shared state. Use conditional edges for branching (e.g., route stimuli generation only when design is approved).
- Integration tips: wrap each capability module as a node; attach human-in-the-loop checks by routing to review nodes; persist checkpoints between runs using the project state service. 
