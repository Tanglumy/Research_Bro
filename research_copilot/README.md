# Research Copilot Backend Service

An AI-powered research workflow system built on SpoonOS that takes researchers from fuzzy ideas to complete experimental designs with synthetic data validation.

## Overview

The Research Copilot provides an end-to-end workflow for behavioral science research:

1. **Literature Explorer** - Extracts concepts, builds knowledge graphs, identifies research gaps
2. **Hypothesis Engine** - Generates structured, testable hypotheses
3. **Design Engine** - Creates experimental designs with validity checks
4. **Stimulus Engine** - Generates balanced experimental stimuli
5. **Simulation Engine** - Produces synthetic participant data for validation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (api.py)                  │
│  REST API endpoints for project management and workflow     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌────────▼────────┐   ┌───────▼────────┐
│    Project   │    │   LLM Manager   │   │   Spoon Tool   │
│ State Service│    │  (OpenAI, etc.) │   │   Integration  │
│  (Persist)   │    └─────────────────┘   │ (Academic API) │
└──────────────┘                           └────────────────┘
        │
        │  Loads/Saves Project State
        │
┌───────▼──────────────────────────────────────────────────┐
│                    Module Pipeline                        │
│  1. Literature Explorer → Knowledge Graph                │
│  2. Hypothesis Engine → Structured Hypotheses            │
│  3. Design Engine → Experimental Design                  │
│  4. Stimulus Engine → Stimulus Bank                      │
│  5. Simulation Engine → Synthetic Data                   │
└──────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

```bash
# Activate SpoonOS environment
source spoon-env/bin/activate

# Install core dependencies
pip install -r spoon-core/requirements.txt

# Install toolkit (for academic search)
pip install -r spoon-toolkit/requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# LLM Provider (required)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
DEEPSEEK_API_KEY=sk-...

# Academic Search (optional, for literature explorer)
SEMANTIC_SCHOLAR_API_KEY=your_key_here
# or other academic API keys
```

## Quick Start

### Start the Backend Server

```bash
# Method 1: Direct python
cd spoon-core
python -m spoon_ai.research_copilot.api

# Method 2: Using uvicorn with auto-reload
uvicorn spoon_ai.research_copilot.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Example Workflow (via API)

#### 1. Create a Project

```bash
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Attachment and Emotion Regulation Study",
    "research_question": "How does attachment anxiety influence emotion regulation strategies in romantic relationships?"
  }'
```

Response:
```json
{
  "id": "abc123...",
  "name": "Attachment and Emotion Regulation Study",
  "status": "created",
  "created_at": "2025-01-23T10:00:00",
  "updated_at": "2025-01-23T10:00:00"
}
```

#### 2. Run Literature Explorer

```bash
curl -X POST "http://localhost:8000/api/workflow/literature-explorer" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "abc123..."
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Literature exploration completed",
  "data": {
    "constructs_found": 5,
    "concepts_mapped": 8,
    "frameworks_identified": 3,
    "citations": 15
  }
}
```

#### 3. Get Project State

```bash
curl "http://localhost:8000/api/projects/abc123..."
```

Returns complete project state including:
- Research question with parsed constructs
- Knowledge graph (nodes and edges)
- Theoretical frameworks
- Common measures
- Research gaps
- Citations

#### 4. Create Checkpoint (Optional)

```bash
curl -X POST "http://localhost:8000/api/projects/abc123.../checkpoints/after-literature"
```

#### 5. Run Full Workflow

```bash
curl -X POST "http://localhost:8000/api/workflow/full" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "abc123..."
  }'
```

## API Reference

### Project Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | POST | Create new project |
| `/api/projects` | GET | List all projects |
| `/api/projects/{id}` | GET | Get project details |
| `/api/projects/{id}` | DELETE | Delete project |

### Workflow Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workflow/literature-explorer` | POST | Extract concepts and build knowledge graph |
| `/api/workflow/hypothesis-engine` | POST | Generate structured hypotheses |
| `/api/workflow/design-engine` | POST | Build experimental design |
| `/api/workflow/stimulus-engine` | POST | Generate stimulus bank |
| `/api/workflow/simulation-engine` | POST | Run synthetic participant simulation |
| `/api/workflow/full` | POST | Execute complete workflow |

### Checkpoint Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects/{id}/checkpoints` | GET | List checkpoints |
| `/api/projects/{id}/checkpoints/{name}` | POST | Create checkpoint |
| `/api/projects/{id}/checkpoints/{name}/restore` | POST | Restore from checkpoint |

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

## Data Models

### ProjectState

Complete state of a research project with versioning:

```python
class ProjectState(BaseModel):
    id: str
    name: str
    status: ProjectStatus  # created, literature_review, hypothesis_generation, etc.
    research_question: Optional[ResearchQuestion]
    literature_landscape: Optional[LiteratureLandscape]
    hypothesis_set: Optional[HypothesisSet]
    experiment_design: Optional[ExperimentDesign]
    stimulus_bank: Optional[StimulusBank]
    simulation_results: Optional[SimulationResults]
    created_at: datetime
    updated_at: datetime
```

### ResearchQuestion

```python
class ResearchQuestion(BaseModel):
    id: str
    raw_text: str
    parsed_constructs: List[str]  # Extracted key concepts
    domain: Optional[str]
    notes: Optional[str]
```

### KnowledgeGraph

```python
class KnowledgeGraph(BaseModel):
    nodes: Dict[str, Concept]  # Theoretical constructs, measures, paradigms
    edges: List[ConceptEdge]   # Relationships (predicts, moderates, etc.)
```

### LiteratureLandscape

Output from Literature Explorer module:

```python
class LiteratureLandscape(BaseModel):
    research_question_id: str
    knowledge_graph: KnowledgeGraph
    theoretical_frameworks: List[Dict[str, Any]]
    common_measures: Dict[str, List[str]]
    experimental_paradigms: List[Dict[str, Any]]
    gaps: LiteratureGap
    summary: str
    citations: List[Dict[str, str]]
```

## Module Details

### 1. Literature Explorer (Implemented)

**Purpose**: Analyze research landscape and build foundational knowledge

**Process**:
1. Extract key constructs from research question
2. Search academic literature using toolkit integration
3. Build knowledge graph with concept relationships
4. Identify theoretical frameworks and measures
5. Detect research gaps
6. Generate summary

**Configuration**:
- Requires LLM provider (OpenAI, Anthropic, or DeepSeek)
- Optional: Academic search API for real literature data
- Falls back to mock data if toolkit unavailable

**Output**:
- Parsed constructs (3-7 key concepts)
- Knowledge graph visualization
- Theoretical frameworks (2-4)
- Common measurement scales
- Research gaps categorized by type
- Academic citations

### 2. Hypothesis Engine (TODO)

**Purpose**: Generate structured, testable hypotheses

**Planned Features**:
- IV/DV/mediator/moderator extraction
- Multiple hypothesis generation
- Direction specification
- Theoretical justification
- Machine-readable output (JSON)

### 3. Design Engine (TODO)

**Purpose**: Build experimental designs with validity checks

**Planned Features**:
- Design type recommendation (between/within/mixed)
- Condition specification
- Measure selection with timing
- Confound detection
- Sample size estimation
- Methods section draft generation

### 4. Stimulus Engine (TODO)

**Purpose**: Generate balanced experimental materials

**Planned Features**:
- Scenario generation with parameters
- Metadata annotation (valence, intensity, etc.)
- Cross-condition balancing
- Multi-language variants
- Quality filtering

### 5. Simulation Engine (TODO)

**Purpose**: Validate design with synthetic data

**Planned Features**:
- Persona modeling (traits, demographics)
- Response simulation
- Effect size estimation
- Weak manipulation detection
- Example response generation

## Project State Storage

### File Structure

```
research_projects/
├── abc123-project-id/
│   ├── state.json              # Current project state
│   └── checkpoints/
│       ├── after-literature.json
│       ├── after-hypotheses.json
│       └── before-stimuli.json
└── def456-another-project/
    └── state.json
```

### Checkpointing

Create checkpoints at key stages:

```python
# Via API
POST /api/projects/{id}/checkpoints/checkpoint-name

# Via Python SDK
from spoon_ai.research_copilot import ProjectStateService

service = ProjectStateService()
service.create_checkpoint(project_id, "after-literature")
service.restore_checkpoint(project_id, "after-literature")
```

## Python SDK Usage

### Direct Module Usage

```python
import asyncio
from spoon_ai.llm import LLMManager, ConfigurationManager
from spoon_ai.research_copilot import (
    ProjectStateService,
    LiteratureExplorer,
    ResearchQuestion
)

async def explore_literature():
    # Initialize services
    llm = LLMManager(ConfigurationManager())
    state_service = ProjectStateService()
    explorer = LiteratureExplorer(llm)
    
    # Create project
    project = state_service.create_project(
        name="My Research",
        research_question_text="How does X affect Y?"
    )
    
    # Run literature exploration
    landscape = await explorer.explore(project.research_question)
    
    # Update project state
    project = state_service.update_literature_landscape(
        project.id,
        landscape
    )
    
    print(f"Found {len(landscape.knowledge_graph.nodes)} concepts")
    print(f"Identified {len(landscape.gaps.missing_combinations)} gaps")
    
    return project

if __name__ == "__main__":
    project = asyncio.run(explore_literature())
```

## Development

### Adding New Modules

1. Create module file in `modules/` directory
2. Implement async `execute()` method
3. Update `models.py` with output schema
4. Add API endpoint in `api.py`
5. Update `__init__.py` exports
6. Add tests

Example module structure:

```python
class HypothesisEngine:
    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
    
    async def generate(self, landscape: LiteratureLandscape) -> HypothesisSet:
        # Implementation
        pass
```

### Testing

Run the backend with test data:

```bash
# Start server
uvicorn spoon_ai.research_copilot.api:app --reload

# In another terminal, run test script
python spoon-core/spoon_ai/research_copilot/examples/test_workflow.py
```

## Troubleshooting

### Common Issues

**Issue**: "Module 'spoon_toolkits' not found"
- **Solution**: Install toolkit: `pip install -r spoon-toolkit/requirements.txt`
- **Alternative**: Backend works without toolkit (uses mock data)

**Issue**: "LLM API key not found"
- **Solution**: Set environment variable (OPENAI_API_KEY, ANTHROPIC_API_KEY, or DEEPSEEK_API_KEY)

**Issue**: "Project state file not found"
- **Solution**: Ensure `research_projects/` directory exists and has write permissions

**Issue**: "Literature search returns no results"
- **Solution**: Check academic API key or rely on LLM-based analysis without external search

## Performance Notes

- **Literature Explorer**: ~30-60 seconds (depends on search API and LLM)
- **Full Workflow**: ~3-5 minutes (when all modules implemented)
- **State Loading**: <100ms (disk I/O)
- **Checkpointing**: <50ms (JSON serialization)

## Security Considerations

1. **API Keys**: Never commit `.env` files; use environment variables in production
2. **CORS**: Configure `allow_origins` in `api.py` for production deployment
3. **Rate Limiting**: Add rate limiting middleware for public deployments
4. **Input Validation**: All inputs validated via Pydantic models
5. **File Permissions**: Ensure `research_projects/` directory has appropriate permissions

## Roadmap

### Version 1.0 (Current)
- [x] Core architecture and data models
- [x] Project state service with checkpointing
- [x] FastAPI backend with REST endpoints
- [x] Literature Explorer module (fully implemented)
- [ ] Hypothesis Engine module
- [ ] Design Engine module
- [ ] Stimulus Engine module
- [ ] Simulation Engine module

### Version 1.1 (Planned)
- [ ] Frontend integration (React/Vue)
- [ ] WebSocket support for real-time updates
- [ ] Graph visualization endpoint
- [ ] Export to Word/PDF
- [ ] Batch project processing

### Version 2.0 (Future)
- [ ] SpoonOS graph orchestration for parallel execution
- [ ] User authentication and multi-tenancy
- [ ] Collaboration features
- [ ] Integration with reference managers (Zotero, Mendeley)
- [ ] Direct export to preregistration platforms

## Contributing

When adding new features:

1. Follow existing code structure and naming conventions
2. Add type hints and docstrings
3. Update this README with new endpoints/features
4. Test with example research questions
5. Create PR with clear description

## License

Part of the SpoonOS/Research Bro project.

## Support

For issues or questions:
- Check `/docs` endpoint for API documentation
- Review example scripts in `examples/` directory
- Open issue on GitHub repository
