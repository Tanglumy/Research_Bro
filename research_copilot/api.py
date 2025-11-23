"""FastAPI Backend Service for Research Copilot.

Provides REST API endpoints for managing research projects and executing
the end-to-end research workflow.
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from spoon_ai.llm import LLMManager, ConfigurationManager
from models import (
    ProjectState,
    ProjectStatus,
    ResearchQuestion,
    LiteratureLandscape,
    HypothesisSet,
    ExperimentDesign,
    StimulusBank,
    SimulationResults
)
from state_service import ProjectStateService
from modules import LiteratureExplorer

logger = logging.getLogger(__name__)

# Global state
state_service: Optional[ProjectStateService] = None
llm_manager: Optional[LLMManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global state_service, llm_manager
    
    # Startup
    logger.info("Initializing Research Copilot Backend...")
    state_service = ProjectStateService()
    llm_manager = LLMManager(ConfigurationManager())
    logger.info("Research Copilot Backend ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Research Copilot Backend")


app = FastAPI(
    title="Research Copilot API",
    description="AI-powered research workflow from idea to experimental design",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    name: str
    research_question: str


class ProjectResponse(BaseModel):
    """Project metadata response."""
    id: str
    name: str
    status: str
    created_at: str
    updated_at: str


class WorkflowRequest(BaseModel):
    """Request to execute workflow module."""
    project_id: str
    parameters: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    """Workflow execution status."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# Project Management Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Research Copilot Backend",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "projects": "/api/projects",
            "workflow": "/api/workflow",
            "docs": "/docs"
        }
    }


@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """Create a new research project.
    
    Args:
        request: Project creation request
        
    Returns:
        Created project metadata
    """
    try:
        project = state_service.create_project(
            name=request.name,
            research_question_text=request.research_question
        )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            status=project.status.value,
            created_at=str(project.created_at),
            updated_at=str(project.updated_at)
        )
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects.
    
    Returns:
        List of project metadata
    """
    try:
        projects = state_service.list_projects()
        return [
            ProjectResponse(
                id=p["id"],
                name=p["name"],
                status=p["status"],
                created_at=p["created_at"],
                updated_at=p["updated_at"]
            )
            for p in projects
        ]
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Complete project state
    """
    try:
        project = state_service.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project.model_dump(mode='json')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        deleted = state_service.delete_project(project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"status": "success", "message": f"Project {project_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Module Endpoints
# ============================================================================

@app.post("/api/workflow/literature-explorer", response_model=WorkflowStatusResponse)
async def run_literature_explorer(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """Execute Literature Explorer module.
    
    Extracts concepts, builds knowledge graph, and identifies research gaps.
    
    Args:
        request: Workflow request with project_id
        background_tasks: FastAPI background tasks
        
    Returns:
        Workflow status and results
    """
    try:
        project = state_service.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.research_question:
            raise HTTPException(status_code=400, detail="Project has no research question")
        
        # Execute literature exploration
        explorer = LiteratureExplorer(llm_manager)
        landscape = await explorer.explore(project.research_question)
        
        # Update project state
        project = state_service.update_literature_landscape(request.project_id, landscape)
        
        # Convert landscape to JSON-serializable dict
        landscape_dict = landscape.model_dump(mode='json')
        
        # Format response to match frontend expectations
        return {
            "status": "success",
            "message": "Literature exploration completed",
            "project_id": request.project_id,
            "module": "literature-explorer",
            "data": {
                "literature_landscape": {
                    "papers": landscape.citations,  # Citations/papers
                    "concepts": [
                        {
                            "id": concept.id,
                            "name": concept.label,
                            "type": concept.type,
                            "related_papers": concept.linked_papers,
                            "measures": concept.common_measures
                        }
                        for concept in landscape.knowledge_graph.nodes.values()
                    ],
                    "relationships": [
                        {
                            "source": edge.source,
                            "target": edge.target,
                            "type": edge.relation_type
                        }
                        for edge in landscape.knowledge_graph.edges
                    ],
                    "frameworks": landscape.theoretical_frameworks,
                    "measures": landscape.common_measures,
                    "paradigms": landscape.experimental_paradigms,
                    "gaps": {
                        "description": landscape.gaps.description,
                        "missing_combinations": landscape.gaps.missing_combinations,
                        "unexplored_populations": landscape.gaps.unexplored_populations,
                        "methodological_gaps": landscape.gaps.methodological_gaps,
                        "theoretical_gaps": landscape.gaps.theoretical_gaps
                    },
                    "summary": landscape.summary
                },
                "metadata": {
                    "constructs_found": len(project.research_question.parsed_constructs),
                    "concepts_mapped": len(landscape.knowledge_graph.nodes),
                    "frameworks_identified": len(landscape.theoretical_frameworks),
                    "citations_count": len(landscape.citations)
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Literature exploration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/hypothesis-engine", response_model=WorkflowStatusResponse)
async def run_hypothesis_engine(request: WorkflowRequest):
    """Execute Hypothesis Engine module.
    
    Generates structured hypotheses from literature landscape.
    
    Args:
        request: Workflow request with project_id
        
    Returns:
        Workflow status and results
    """
    try:
        project = state_service.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.literature_landscape:
            raise HTTPException(status_code=400, detail="Run literature explorer first")
        
        # TODO: Implement hypothesis generation
        # For now, return placeholder
        return WorkflowStatusResponse(
            status="pending",
            message="Hypothesis engine not yet implemented",
            data={"note": "Module implementation in progress"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hypothesis generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/design-engine", response_model=WorkflowStatusResponse)
async def run_design_engine(request: WorkflowRequest):
    """Execute Design Engine module.
    
    Builds experimental design from hypotheses.
    
    Args:
        request: Workflow request with project_id
        
    Returns:
        Workflow status and results
    """
    try:
        project = state_service.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.hypothesis_set:
            raise HTTPException(status_code=400, detail="Run hypothesis engine first")
        
        # TODO: Implement design building
        return WorkflowStatusResponse(
            status="pending",
            message="Design engine not yet implemented",
            data={"note": "Module implementation in progress"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Design building failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/stimulus-engine", response_model=WorkflowStatusResponse)
async def run_stimulus_engine(request: WorkflowRequest):
    """Execute Stimulus Engine module.
    
    Generates balanced stimulus bank.
    
    Args:
        request: Workflow request with project_id and parameters
        
    Returns:
        Workflow status and results
    """
    try:
        project = state_service.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.experiment_design:
            raise HTTPException(status_code=400, detail="Run design engine first")
        
        # TODO: Implement stimulus generation
        return WorkflowStatusResponse(
            status="pending",
            message="Stimulus engine not yet implemented",
            data={"note": "Module implementation in progress"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stimulus generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/simulation-engine", response_model=WorkflowStatusResponse)
async def run_simulation_engine(request: WorkflowRequest):
    """Execute Simulation Engine module.
    
    Generates synthetic participant data.
    
    Args:
        request: Workflow request with project_id and parameters
        
    Returns:
        Workflow status and results
    """
    try:
        project = state_service.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.stimulus_bank:
            raise HTTPException(status_code=400, detail="Run stimulus engine first")
        
        # TODO: Implement simulation
        return WorkflowStatusResponse(
            status="pending",
            message="Simulation engine not yet implemented",
            data={"note": "Module implementation in progress"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/full", response_model=WorkflowStatusResponse)
async def run_full_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """Execute the complete end-to-end workflow.
    
    Runs all modules in sequence: Literature -> Hypotheses -> Design -> Stimuli -> Simulation
    
    Args:
        request: Workflow request with project_id
        background_tasks: FastAPI background tasks
        
    Returns:
        Workflow status
    """
    try:
        project = state_service.load_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # For now, just run literature explorer
        # Full workflow orchestration will be implemented with remaining modules
        explorer = LiteratureExplorer(llm_manager)
        landscape = await explorer.explore(project.research_question)
        project = state_service.update_literature_landscape(request.project_id, landscape)
        
        return WorkflowStatusResponse(
            status="partial",
            message="Full workflow partially implemented - literature exploration completed",
            data={
                "completed_modules": ["literature_explorer"],
                "pending_modules": ["hypothesis_engine", "design_engine", "stimulus_engine", "simulation_engine"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Checkpoint Management
# ============================================================================

@app.post("/api/projects/{project_id}/checkpoints/{checkpoint_name}")
async def create_checkpoint(project_id: str, checkpoint_name: str):
    """Create a checkpoint of current project state.
    
    Args:
        project_id: Project identifier
        checkpoint_name: Name for the checkpoint
        
    Returns:
        Checkpoint confirmation
    """
    try:
        state_service.create_checkpoint(project_id, checkpoint_name)
        return {
            "status": "success",
            "message": f"Checkpoint '{checkpoint_name}' created"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/checkpoints/{checkpoint_name}/restore")
async def restore_checkpoint(project_id: str, checkpoint_name: str):
    """Restore project from a checkpoint.
    
    Args:
        project_id: Project identifier
        checkpoint_name: Checkpoint to restore
        
    Returns:
        Restoration confirmation
    """
    try:
        project = state_service.restore_checkpoint(project_id, checkpoint_name)
        return {
            "status": "success",
            "message": f"Project restored from checkpoint '{checkpoint_name}'",
            "project_status": project.status.value
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/checkpoints")
async def list_checkpoints(project_id: str):
    """List all checkpoints for a project.
    
    Args:
        project_id: Project identifier
        
    Returns:
        List of checkpoint names
    """
    try:
        checkpoints = state_service.list_checkpoints(project_id)
        return {"checkpoints": checkpoints}
    except Exception as e:
        logger.error(f"Failed to list checkpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "research-copilot-backend",
        "state_service": "operational" if state_service else "not initialized",
        "llm_manager": "operational" if llm_manager else "not initialized"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
