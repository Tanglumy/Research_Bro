# Backend API Contract

This document defines the exact API contract that the frontend expects from the backend. All responses must be valid JSON strings.

## 🚨 Critical: JSON Serialization

**All endpoint responses MUST return properly serialized JSON strings**, not Python objects.

### ❌ Common Error

```python
# This will cause: "the JSON object must be str, bytes or bytearray, not LLMResponse"
llm_response = await llm_manager.execute(...)
return llm_response  # LLMResponse object - NOT JSON serializable!
```

### ✅ Correct Approach

```python
from fastapi.responses import JSONResponse

# Option 1: Extract content from LLM response
llm_response = await llm_manager.execute(...)
return JSONResponse(content={
    "status": "success",
    "message": "Completed",
    "data": llm_response.content  # or llm_response.to_dict()
})

# Option 2: Use Pydantic models (recommended)
from pydantic import BaseModel

class WorkflowResponse(BaseModel):
    status: str
    message: str
    data: dict

result = WorkflowResponse(
    status="success",
    message="Completed",
    data=extracted_data
)
return result  # FastAPI auto-serializes Pydantic models
```

---

## 📋 Type Definitions

The frontend uses TypeScript. Here are the exact types your backend responses must match:

### Project Type

```typescript
interface Project {
    id: string;
    name: string;
    research_question: string;
    status: string;
    created_at: string;
    updated_at: string;
    
    // Optional workflow results (populated after modules complete)
    literature_landscape?: LiteratureLandscape;
    hypotheses?: Hypothesis[];
    experimental_design?: ExperimentalDesign;
    stimuli?: Stimulus[];
    simulation_results?: SimulationResults;
}
```

### WorkflowResult Type

```typescript
interface WorkflowResult {
    status: string;           // "success" | "error" | "running"
    message: string;          // Human-readable message
    data?: any;               // Module-specific data
    project_id?: string;      // ID of the project
    module?: string;          // Module name
}
```

---

## 🔌 Endpoint Specifications

### 1. Create Project

**Endpoint:** `POST /api/projects`

**Request:**
```json
{
    "name": "My Research Project",
    "research_question": "How does meditation affect cortisol levels?"
}
```

**Response:** (Status 200)
```json
{
    "id": "uuid-here",
    "name": "My Research Project",
    "research_question": "How does meditation affect cortisol levels?",
    "status": "created",
    "created_at": "2025-11-23 10:30:00.123456",
    "updated_at": "2025-11-23 10:30:00.123456"
}
```

**Python Backend Example:**
```python
from pydantic import BaseModel
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    research_question: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    research_question: str
    status: str
    created_at: str
    updated_at: str

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    new_project = {
        "id": str(uuid.uuid4()),
        "name": project.name,
        "research_question": project.research_question,
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    # Save to database...
    return new_project
```

---

### 2. Get Project

**Endpoint:** `GET /api/projects/{project_id}`

**Response:** (Status 200)
```json
{
    "id": "uuid-here",
    "name": "My Research Project",
    "research_question": "How does meditation affect cortisol levels?",
    "status": "completed",
    "created_at": "2025-11-23 10:30:00.123456",
    "updated_at": "2025-11-23 11:45:00.789012",
    
    "literature_landscape": {
        "papers": [...],
        "concepts": [...],
        "gaps": [...]
    },
    "hypotheses": [...],
    "experimental_design": {...},
    "stimuli": [...],
    "simulation_results": {...}
}
```

**Important:** Include all completed workflow results in the project response.

---

### 3. List Projects

**Endpoint:** `GET /api/projects`

**Response:** (Status 200)
```json
[
    {
        "id": "uuid-1",
        "name": "Project 1",
        "research_question": "Question 1?",
        "status": "completed",
        "created_at": "2025-11-23 10:30:00",
        "updated_at": "2025-11-23 11:45:00"
    },
    {
        "id": "uuid-2",
        "name": "Project 2",
        "research_question": "Question 2?",
        "status": "running",
        "created_at": "2025-11-23 12:00:00",
        "updated_at": "2025-11-23 12:15:00"
    }
]
```

---

### 4. Delete Project

**Endpoint:** `DELETE /api/projects/{project_id}`

**Response:** (Status 200)
```json
{
    "message": "Project deleted successfully"
}
```

---

## 🔄 Workflow Endpoints

All workflow endpoints follow the same pattern:

### Request Format

**Endpoint:** `POST /api/workflow/{module-name}`

Where `{module-name}` is one of:
- `literature-explorer`
- `hypothesis-engine`
- `design-engine`
- `stimulus-engine`
- `simulation-engine`
- `full` (runs all modules)

**Request Body:**
```json
{
    "project_id": "uuid-here",
    "parameters": {
        // Module-specific parameters (optional)
    }
}
```

### Response Format

**Success Response:** (Status 200)
```json
{
    "status": "success",
    "message": "Literature exploration completed successfully",
    "project_id": "uuid-here",
    "module": "literature-explorer",
    "data": {
        // Module-specific data structure (see below)
    }
}
```

**Error Response:** (Status 500)
```json
{
    "detail": "Error message describing what went wrong"
}
```

---

## 📊 Module-Specific Data Structures

### 1. Literature Explorer

**Response `data` field:**
```json
{
    "literature_landscape": {
        "papers": [
            {
                "id": "paper-1",
                "title": "Effects of Meditation on Stress",
                "authors": ["Smith, J.", "Doe, A."],
                "year": "2023",
                "journal": "Journal of Neuroscience",
                "citations": 47,
                "relevance_score": 0.92,
                "key_findings": ["Finding 1", "Finding 2"],
                "methodology": "Randomized controlled trial",
                "url": "https://doi.org/..."
            }
        ],
        "concepts": [
            {
                "id": "concept-1",
                "name": "Cortisol Regulation",
                "definition": "The body's process of...",
                "related_papers": ["paper-1", "paper-2"],
                "importance": 0.85
            }
        ],
        "gaps": [
            {
                "id": "gap-1",
                "description": "Limited research on long-term effects...",
                "severity": "high",
                "related_concepts": ["concept-1"]
            }
        ]
    }
}
```

**Python Backend Example:**
```python
@app.post("/api/workflow/literature-explorer")
async def run_literature_explorer(request: WorkflowRequest):
    # Execute LLM workflow
    llm_response = await llm_manager.execute(
        prompt=f"Explore literature for: {project.research_question}"
    )
    
    # ❌ DON'T: return llm_response (not JSON serializable)
    
    # ✅ DO: Extract and structure the data
    literature_data = parse_llm_response(llm_response)  # Your parsing logic
    
    return {
        "status": "success",
        "message": "Literature exploration completed",
        "project_id": request.project_id,
        "module": "literature-explorer",
        "data": {
            "literature_landscape": literature_data
        }
    }
```

---

### 2. Hypothesis Engine

**Response `data` field:**
```json
{
    "hypotheses": [
        {
            "id": "hyp-1",
            "hypothesis": "Regular meditation reduces cortisol levels by 20%",
            "rationale": "Based on 12 studies showing...",
            "testability": 0.9,
            "novelty": 0.7,
            "feasibility": 0.85,
            "supporting_evidence": ["paper-1", "paper-3"]
        }
    ]
}
```

---

### 3. Design Engine

**Response `data` field:**
```json
{
    "experimental_design": {
        "design_type": "Randomized Controlled Trial",
        "independent_variables": [
            {
                "name": "Meditation Duration",
                "type": "continuous",
                "levels": ["10 min", "20 min", "30 min"]
            }
        ],
        "dependent_variables": [
            {
                "name": "Cortisol Level",
                "measurement": "Salivary cortisol (μg/dL)",
                "timing": "Pre and post intervention"
            }
        ],
        "sample_size": 120,
        "duration": "8 weeks",
        "control_group": true,
        "blinding": "single-blind"
    }
}
```

---

### 4. Stimulus Engine

**Response `data` field:**
```json
{
    "stimuli": [
        {
            "id": "stim-1",
            "name": "Meditation Audio Guide",
            "type": "audio",
            "description": "10-minute guided meditation...",
            "file_url": "https://...",
            "parameters": {
                "duration": "10 minutes",
                "voice": "neutral",
                "background": "nature sounds"
            }
        }
    ]
}
```

---

### 5. Simulation Engine

**Response `data` field:**
```json
{
    "simulation_results": {
        "power_analysis": {
            "statistical_power": 0.85,
            "effect_size": 0.6,
            "required_sample_size": 120
        },
        "expected_outcomes": [
            {
                "condition": "Meditation Group",
                "predicted_mean": 12.5,
                "confidence_interval": [11.2, 13.8]
            }
        ],
        "visualizations": [
            {
                "type": "power_curve",
                "data_url": "https://..."
            }
        ]
    }
}
```

---

## 🔧 Common Backend Issues & Fixes

### Issue 1: `'dict' object has no attribute 'role'`

**Cause:** LLM message format is incorrect

**Fix:**
```python
# ❌ Wrong
messages = {"role": "user", "content": "..."}

# ✅ Correct
messages = [{"role": "user", "content": "..."}]  # Must be a list!
```

---

### Issue 2: `the JSON object must be str, bytes or bytearray, not LLMResponse`

**Cause:** Returning non-serializable Python objects

**Fix:**
```python
# ❌ Wrong
return llm_response  # LLMResponse object

# ✅ Correct - Option 1: Extract content
return {
    "status": "success",
    "data": llm_response.content
}

# ✅ Correct - Option 2: Convert to dict
return {
    "status": "success",
    "data": llm_response.model_dump()  # or .dict() for older Pydantic
}

# ✅ Correct - Option 3: Manual extraction
return {
    "status": "success",
    "data": {
        "literature_landscape": parse_response(llm_response.content)
    }
}
```

---

### Issue 3: Frontend gets `undefined` for expected fields

**Cause:** Response structure doesn't match TypeScript types

**Fix:** Ensure your response exactly matches the structures defined above. Use the browser console to see what the frontend expects vs. what it receives.

---

## ✅ Testing Your Backend

Use these curl commands to test your endpoints:

```bash
# 1. Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "research_question": "Test question?"}'

# 2. Run literature explorer (replace PROJECT_ID)
curl -X POST http://localhost:8000/api/workflow/literature-explorer \
  -H "Content-Type: application/json" \
  -d '{"project_id": "PROJECT_ID", "parameters": {}}'

# 3. Get updated project
curl http://localhost:8000/api/projects/PROJECT_ID
```

**Expected:** All responses should be valid JSON that can be parsed with `| jq .`

---

## 📞 Need Help?

If the frontend shows errors, check:

1. **Backend logs** - What error is the backend actually throwing?
2. **Browser console** - The frontend logs all API calls with `[API]` prefix
3. **Response format** - Does your JSON match the TypeScript types exactly?
4. **Status codes** - Frontend expects 200 for success, 500 for errors

**Pro tip:** Use `console.log(JSON.stringify(response, null, 2))` in your backend to see exactly what you're sending.
