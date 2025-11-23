# Research Copilot Multi-Agent Workflow (SpoonOS Prototype)

## Goal
Robust, generalizable workflow from research idea → literature → hypotheses → design → stimuli → simulation with checkpoints, validation, and human-in-loop options.

## Agents (nodes)
- **SupervisorAgent (GraphAgent)**: orchestrates StateGraph, checkpoints, retries, human pauses.
- **LiteratureAgent**: runs Research academic/web, builds concept nodes/edges, gaps, measures.
- **HypothesisAgent**: generates structured hypotheses (IV/DV/mediator/moderator/direction) from concept slice + intent.
- **DesignAgent**: proposes design type, conditions, measures/timepoints, confound report, sample size heuristics, Methods draft.
- **StimulusAgent**: generates/balances stimuli with metadata; safety filters and balance report.
- **SimulationAgent**: builds persona mix, simulates DVs/text, flags weak effects/dead vars.

## State & contracts
`ProjectState` snapshot after each node:
```json
{
  "project_id": "...",
  "rq": {...},
  "concepts": {"nodes": [], "edges": []},
  "hypotheses": [],
  "design": {},
  "stimuli": [],
  "simulation": {},
  "audit_log": [],
  "checkpoint_id": "..."
}
```
Validate with Pydantic; store errors in `audit_log`.

## Workflow (StateGraph)
1) `ingest_rq` → normalize text, extract constructs (must yield parsed_constructs).  
2) `literature` → concept graph + gaps (require ≥1 node or flag needs_user_input).  
3) `hypotheses` → ≥2 hypotheses with IV/DV/direction.  
4) `design` → design_type, conditions≥2, measures/timepoints, confound_report, N ranges, Methods draft.  
5) `stimuli` → N/condition, metadata complete, safety filter, balance_report.  
6) `simulate` → persona plan, means/SDs, dead_vars, weak_effects, sample responses.  
7) `review_export` → bundle JSON/CSV/MD + audit_log + checkpoint pointer.  
Conditional edges: on validation fail → `needs_revision` (ask user/adjust) → resume.

## Reliability patterns
- LLM fallback chain: openai → anthropic → deepseek; temp ≤0.3 for structured steps.
- Retries: max 2 with jitter on HTTP/tool errors; degrade gracefully when optional keys missing.
- Checkpoints: per-node state persisted; idempotent writes for that segment only.
- Observability: enable debug logging/metrics; per-node timings into `audit_log`.
- Human-in-loop: pauses after design and stimuli unless `auto_continue`; optional notify via Discord/Email.

## Tools (Spoon Toolkit)
- Retrieval: `ResearchAcademicSearchTool`, `ResearchAISearchTool`.
- Notifications: `DiscordTool`, `EmailTool`.
- Storage (optional): `Aioz/Foureverland/Oort` for artifact dumps.
- GitHub (optional): `GetGitHubIssues/PRs/Commits` for repo sync.

## Security/config
- Require LLM keys (OpenAI/Anthropic/DeepSeek). Use env vars/.env; never commit.
- Retrieval keys optional (Chainbase only if on-chain features used).
- Validate env presence at init; fail fast with actionable error.
