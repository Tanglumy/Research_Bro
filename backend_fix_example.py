"""
Backend Fix Example for JSON Serialization Issue

This file shows how to fix the current error:
"the JSON object must be str, bytes or bytearray, not LLMResponse"

Problem: The backend is returning LLMResponse objects directly,
which are not JSON-serializable.

Solution: Extract the content from LLMResponse and return a proper dictionary.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()

# ============================================================
# Request/Response Models
# ============================================================

class WorkflowRequest(BaseModel):
    project_id: str
    parameters: Dict[str, Any] = {}

class WorkflowResponse(BaseModel):
    status: str
    message: str
    project_id: str
    module: str
    data: Optional[Dict[str, Any]] = None


# ============================================================
# ❌ WRONG: This causes the serialization error
# ============================================================

@app.post("/api/workflow/literature-explorer-BROKEN")
async def run_literature_explorer_broken(request: WorkflowRequest):
    """
    This will cause: "the JSON object must be str, bytes or bytearray, not LLMResponse"
    """
    # Get project from database
    project = await get_project(request.project_id)
    
    # Execute LLM
    llm_response = await llm_manager.execute(
        prompt=f"Explore literature for: {project.research_question}"
    )
    
    # ❌ PROBLEM: Returning LLMResponse object directly
    return llm_response  # This is NOT JSON serializable!


# ============================================================
# ✅ CORRECT: Option 1 - Extract content string
# ============================================================

@app.post("/api/workflow/literature-explorer")
async def run_literature_explorer_v1(request: WorkflowRequest):
    """
    Fix: Extract the text content from LLMResponse
    """
    # Get project from database
    project = await get_project(request.project_id)
    
    # Execute LLM
    llm_response = await llm_manager.execute(
        prompt=f"Explore literature for: {project.research_question}"
    )
    
    # ✅ SOLUTION: Extract content from LLMResponse
    # The exact attribute name depends on your LLM library:
    # - For OpenAI: llm_response.choices[0].message.content
    # - For Anthropic: llm_response.content[0].text
    # - For custom wrapper: llm_response.content or llm_response.text
    
    content_text = llm_response.content  # Adjust based on your LLM library
    
    # Parse the LLM response into structured data
    # (Assuming LLM returns JSON string or you have a parser)
    import json
    try:
        literature_data = json.loads(content_text)
    except json.JSONDecodeError:
        # If LLM didn't return valid JSON, create a basic structure
        literature_data = {
            "papers": [],
            "concepts": [],
            "gaps": []
        }
    
    # Return proper JSON structure
    return {
        "status": "success",
        "message": "Literature exploration completed",
        "project_id": request.project_id,
        "module": "literature-explorer",
        "data": {
            "literature_landscape": literature_data
        }
    }


# ============================================================
# ✅ CORRECT: Option 2 - Use Pydantic response model
# ============================================================

@app.post("/api/workflow/literature-explorer-v2", response_model=WorkflowResponse)
async def run_literature_explorer_v2(request: WorkflowRequest):
    """
    Fix: Use Pydantic model for automatic serialization
    """
    project = await get_project(request.project_id)
    
    # Execute LLM
    llm_response = await llm_manager.execute(
        prompt=f"Explore literature for: {project.research_question}"
    )
    
    # Extract and parse content
    content_text = llm_response.content
    literature_data = parse_literature_response(content_text)
    
    # ✅ SOLUTION: Create Pydantic model instance
    # FastAPI automatically serializes Pydantic models to JSON
    return WorkflowResponse(
        status="success",
        message="Literature exploration completed",
        project_id=request.project_id,
        module="literature-explorer",
        data={"literature_landscape": literature_data}
    )


# ============================================================
# ✅ CORRECT: Option 3 - Use JSONResponse explicitly
# ============================================================

@app.post("/api/workflow/literature-explorer-v3")
async def run_literature_explorer_v3(request: WorkflowRequest):
    """
    Fix: Use JSONResponse for explicit control
    """
    try:
        project = await get_project(request.project_id)
        
        # Execute LLM
        llm_response = await llm_manager.execute(
            prompt=f"Explore literature for: {project.research_question}"
        )
        
        # Extract content
        content_text = llm_response.content
        literature_data = parse_literature_response(content_text)
        
        # ✅ SOLUTION: Explicitly return JSONResponse
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Literature exploration completed",
                "project_id": request.project_id,
                "module": "literature-explorer",
                "data": {
                    "literature_landscape": literature_data
                }
            }
        )
    except Exception as e:
        # Proper error handling
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(e)
            }
        )


# ============================================================
# Helper Functions
# ============================================================

async def get_project(project_id: str):
    """Fetch project from database"""
    # Your database logic here
    pass

def parse_literature_response(content: str) -> dict:
    """
    Parse LLM response into structured literature data
    
    The LLM should return JSON in this format:
    {
        "papers": [
            {
                "id": "...",
                "title": "...",
                "authors": ["..."],
                "year": "2023",
                "journal": "...",
                "citations": 47,
                "relevance_score": 0.92,
                "key_findings": ["..."],
                "methodology": "...",
                "url": "https://..."
            }
        ],
        "concepts": [
            {
                "id": "...",
                "name": "...",
                "definition": "...",
                "related_papers": ["..."],
                "importance": 0.85
            }
        ],
        "gaps": [
            {
                "id": "...",
                "description": "...",
                "severity": "high",
                "related_concepts": ["..."]
            }
        ]
    }
    """
    import json
    
    try:
        # Try to parse as JSON
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        # If not JSON, you might need to extract it from markdown or text
        # This is a simple example - adjust based on your LLM output format
        
        # Example: Extract JSON from markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            json_str = content[start:end].strip()
            return json.loads(json_str)
        
        # Fallback: return empty structure
        return {
            "papers": [],
            "concepts": [],
            "gaps": []
        }


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    """
    Test your endpoint with:
    
    curl -X POST http://localhost:8000/api/workflow/literature-explorer \
      -H "Content-Type: application/json" \
      -d '{"project_id": "test-id", "parameters": {}}'
    
    Expected output:
    {
        "status": "success",
        "message": "Literature exploration completed",
        "project_id": "test-id",
        "module": "literature-explorer",
        "data": {
            "literature_landscape": {
                "papers": [...],
                "concepts": [...],
                "gaps": [...]
            }
        }
    }
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
