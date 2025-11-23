# Feature To-Do (Research Copilot on SpoonOS)

> Build in a new top-level package (e.g., `copilot_workflow/`) to avoid changing `spoon-core`.

## Package setup
- [x] Create `copilot_workflow/` package with `__init__.py` and README stub.
- [x] Add `schemas.py` (Pydantic models for RQ, concepts/edges, hypotheses, design, stimuli, personas/simulation, project state, audit entries) and `validation.py`.

## Workflow graph
- [x] Implement `workflow.py` using SpoonOS `StateGraph` imported from `spoon_core` (read-only usage). Nodes: ingest_rq → literature → hypotheses → design → stimuli → simulate → review_export.
- [x] Research Question Ingestion node fully implemented with Gemini integration
- [ ] Add conditional edges to `needs_revision` on validation failures; wire checkpoint IDs into state snapshots.

## Module nodes (stub → real)

### PHASE 1: Infrastructure & Configuration [IN PROGRESS]
- [ ] **Create `copilot_workflow/config.py`** - Centralized config loading
  - Load GEMINI_API_KEY (required) with validation
  - Load Research keys (optional with fallback)
  - Load toolkit keys (storage, social) with graceful degradation
  - Fail fast with clear errors for missing required keys
  - Log which providers/tools are available

- [ ] **Add retry decorator with exponential backoff**
  - LLM API calls (rate limits, transient failures)
  - Academic search API calls (network issues)
  - Tool executions (temporary unavailability)
  - Log all fallback actions to audit trail

- [ ] **Observability & Monitoring**
  - Add timing metrics to each graph node
  - Log validation results to audit trail with context
  - Create debug mode flag for verbose LLM prompt/response logging
  - Add progress indicators for long-running operations

### PHASE 2: Module 1 - Literature Landscape Explorer [NEXT PRIORITY]

#### Structure Setup
- [ ] Create `Literature_Landscape_Explorer/` directory
- [ ] Create `__init__.py` (module exports)
- [ ] Create `run.py` (main async run(project_state) function)
- [ ] Create `paper_retrieval.py` (Research integration)
- [ ] Create `concept_extraction.py` (Gemini-powered analysis)
- [ ] Create `graph_builder.py` (build ConceptNode/ConceptEdge)
- [ ] Create `gap_analysis.py` (compare RQ with existing literature)

#### Implementation Tasks
- [ ] **Paper Retrieval** (paper_retrieval.py)
  - Integrate `ResearchAcademicSearchTool` from spoon-toolkit
  - Query using constructs from ResearchQuestion
  - Retrieve top 20-30 relevant papers with abstracts
  - Handle API failures gracefully (retry + cache)
  - Return list of paper metadata (title, authors, abstract, year, DOI)

- [ ] **Concept Extraction** (concept_extraction.py)
  - Use Gemini to analyze paper abstracts
  - Extract: theoretical frameworks, measures, experimental paradigms
  - Identify operationalizations (how constructs are measured/manipulated)
  - Map to existing ConceptNode schema
  - Deduplicate similar concepts (e.g., "attachment anxiety" vs "anxious attachment")

- [ ] **Graph Building** (graph_builder.py)
  - Create ConceptNode for each unique construct
  - Create ConceptEdge for relationships (predicts, moderates, mediates)
  - Link papers to relevant concept nodes
  - Store in project.concepts dict (nodes + edges)

- [ ] **Gap Analysis** (gap_analysis.py)
  - Compare RQ constructs with literature coverage
  - Identify: untested IV-DV combinations, missing populations, novel contexts
  - Generate human-readable gap summary
  - Flag if research question is too derivative vs too novel

#### Integration & Testing
- [ ] Update `copilot_workflow/workflow.py` literature_node
  - Call Literature_Landscape_Explorer.run(project)
  - Handle errors gracefully (log + continue with partial data)
  - Update project.concepts with graph data
  - Add audit log entries for papers retrieved, concepts extracted

- [ ] Create `tests/test_literature_explorer.py`
  - Test paper retrieval with real Research API
  - Test concept extraction with sample abstracts
  - Test graph building with mock data
  - Test gap analysis logic
  - End-to-end test: RQ → literature landscape

### PHASE 3: Module 2 - Hypothesis Generator & Structurer
- [ ] Implement `Hypothesis_Generator_Structurer/run()` function
- [ ] Use Gemini to decompose constructs into IV/DV/mediators/moderators
- [ ] Generate multiple structured hypotheses with theoretical justification
- [ ] Export hypotheses as JSON and human-readable table
- [ ] Validate hypothesis objects match schema requirements
- [ ] Link hypotheses to theoretical basis from literature (Module 1 output)

### PHASE 4: Module 3 - Design Builder & Critic
- [ ] Design module: propose design type, conditions, measures/timepoints, confound report, N heuristics, Methods draft.
- [ ] Propose design type (between/within/mixed) based on hypotheses
- [ ] Define conditions, manipulations, and measurement time points
- [ ] Check for confounds (manipulation length, tone, etc.)
- [ ] Generate sample size heuristics (power analysis)
- [ ] Draft Methods section in APA format

### PHASE 5: Module 4 - Stimulus Factory
- [ ] Stimulus module: generate/balance stimuli with metadata; safety filter; balance report.
- [ ] Generate scenario texts with systematic variation
- [ ] Annotate stimuli with metadata (valence, intensity, relationship type)
- [ ] Balance distributions across conditions
- [ ] Filter ethically problematic content
- [ ] Support multi-language generation

### PHASE 6: Module 5 - Synthetic Participant Simulator
- [ ] Simulation module: persona plan, synthetic data, dead_vars/weak_effects, sample responses.
- [ ] Define persona templates (attachment styles, traits, culture)
- [ ] Simulate responses for each condition
- [ ] Compute condition means/SDs and effect estimates
- [ ] Flag dead variables and weak manipulations
- [ ] Generate example free-text responses

### PHASE 7: Review/Export Module
- [ ] Review/export module: bundle JSON/CSV/MD, audit entries, checkpoint pointer.
- [ ] Export knowledge graph slices + citations
- [ ] Export hypothesis tables / JSON
- [ ] Export design tables + Methods draft
- [ ] Export stimulus banks + metadata
- [ ] Export synthetic result summaries

## Workflow Enhancements
- [ ] Add conditional edges to `needs_revision` on validation failures
- [ ] Wire checkpoint IDs into state snapshots
- [ ] Implement checkpoint saving after each successful module
- [ ] Store checkpoints in `~/.adal/research_copilot/checkpoints/`
- [ ] Add resume functionality: load project state from checkpoint ID
- [ ] Test workflow interruption and resume

## Human-in-loop & notifications
- [ ] Add pause points after design and stimuli when `auto_continue` is false.
- [ ] Optional notify node using `DiscordTool`/`EmailTool` with concise status summaries.
- [ ] Make notifications opt-in via config flag

## Demo & docs
- [ ] Provide `demo.py` to run full chain with sample input and resume-from-checkpoint option.
- [ ] Document required env vars, provider settings, and prompts per node in package README.
- [ ] Update `copilot_workflow/README.md` with Gemini-specific notes
- [ ] Add usage examples showing successful construct extraction
- [ ] Document known limitations (rate limits, JSON format handling)
- [ ] Create `docs/module_specs/` directory with detailed specs for each module

## Testing Strategy
- [x] `tests/test_ingest_rq.py` - Research question ingestion (PASSING)
- [ ] `tests/test_literature_explorer.py` - Literature module
- [ ] `tests/test_hypothesis_generator.py` - Hypothesis module
- [ ] `tests/test_design_builder.py` - Design module
- [ ] `tests/test_stimulus_factory.py` - Stimulus module
- [ ] `tests/test_simulation.py` - Simulation module
- [ ] End-to-end integration tests

## Success Metrics

### Module 1 Completion Criteria
- [ ] Can retrieve 20+ relevant papers for sample RQ
- [ ] Extracts 5-10 unique concepts with relationships
- [ ] Builds valid graph (ConceptNode + ConceptEdge objects)
- [ ] Generates actionable gap summary
- [ ] All tests passing
- [ ] Handles API failures gracefully

### Overall System Health
- [x] Research question ingestion working with Gemini
- [ ] All 5 modules integrated in workflow
- [ ] End-to-end test: RQ → literature → hypotheses → design → stimuli → simulation → export
- [ ] No rate limit errors (proper backoff implemented)
- [ ] Clear error messages for missing configs
- [ ] Audit logs contain useful debugging info
- [ ] Can resume workflow from any checkpoint

## Current Status (as of last update)
- ✅ Research Question Ingestion (Module 0) - COMPLETE
- ✅ Gemini integration working with JSON parsing
- ✅ Test suite for ingestion passing (3/3 tests)
- ✅ Core workflow graph structure exists
- 🔄 Next: Implement config.py and start Module 1 (Literature Explorer)
