"""Project State Service for Research Copilot.

Provides persistence and management for research project state,
enabling versioning, checkpointing, and state transitions.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

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

logger = logging.getLogger(__name__)


class ProjectStateService:
    """Manages research project state with versioning and persistence."""
    
    def __init__(self, storage_dir: str = "./research_projects"):
        """Initialize the state service.
        
        Args:
            storage_dir: Directory for storing project state files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ProjectStateService initialized with storage at {self.storage_dir}")
    
    def _get_project_dir(self, project_id: str) -> Path:
        """Get the directory for a specific project."""
        return self.storage_dir / project_id
    
    def _get_state_file(self, project_id: str) -> Path:
        """Get the main state file for a project."""
        return self._get_project_dir(project_id) / "state.json"
    
    def _get_checkpoint_file(self, project_id: str, checkpoint_name: str) -> Path:
        """Get a checkpoint file path."""
        checkpoints_dir = self._get_project_dir(project_id) / "checkpoints"
        checkpoints_dir.mkdir(exist_ok=True)
        return checkpoints_dir / f"{checkpoint_name}.json"
    
    def create_project(self, name: str, research_question_text: str) -> ProjectState:
        """Create a new research project.
        
        Args:
            name: Project name
            research_question_text: Initial research question
            
        Returns:
            Created ProjectState
        """
        project_id = str(uuid.uuid4())
        rq_id = str(uuid.uuid4())
        
        research_question = ResearchQuestion(
            id=rq_id,
            raw_text=research_question_text
        )
        
        project = ProjectState(
            id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            research_question=research_question
        )
        
        self.save_project(project)
        logger.info(f"Created project {project_id}: {name}")
        return project
    
    def save_project(self, project: ProjectState) -> None:
        """Save project state to disk.
        
        Args:
            project: Project state to save
        """
        project_dir = self._get_project_dir(project.id)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = self._get_state_file(project.id)
        with open(state_file, 'w') as f:
            json.dump(project.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.debug(f"Saved project {project.id}")
    
    def load_project(self, project_id: str) -> Optional[ProjectState]:
        """Load project state from disk.
        
        Args:
            project_id: Project identifier
            
        Returns:
            ProjectState if found, None otherwise
        """
        state_file = self._get_state_file(project_id)
        if not state_file.exists():
            logger.warning(f"Project {project_id} not found")
            return None
        
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        project = ProjectState(**data)
        logger.debug(f"Loaded project {project_id}")
        return project
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with basic metadata.
        
        Returns:
            List of project metadata dictionaries
        """
        projects = []
        for project_dir in self.storage_dir.iterdir():
            if project_dir.is_dir():
                state_file = project_dir / "state.json"
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        data = json.load(f)
                        projects.append({
                            "id": data["id"],
                            "name": data["name"],
                            "status": data["status"],
                            "created_at": data["created_at"],
                            "updated_at": data["updated_at"]
                        })
        return sorted(projects, key=lambda p: p["updated_at"], reverse=True)
    
    def update_research_question(self, project_id: str, research_question: ResearchQuestion) -> ProjectState:
        """Update research question for a project.
        
        Args:
            project_id: Project identifier
            research_question: Updated research question
            
        Returns:
            Updated ProjectState
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project.research_question = research_question
        project.updated_at = datetime.utcnow()
        self.save_project(project)
        return project
    
    def update_literature_landscape(self, project_id: str, landscape: LiteratureLandscape) -> ProjectState:
        """Update literature landscape for a project.
        
        Args:
            project_id: Project identifier
            landscape: Literature landscape output
            
        Returns:
            Updated ProjectState
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project.literature_landscape = landscape
        project.update_status(ProjectStatus.LITERATURE_REVIEW)
        self.save_project(project)
        logger.info(f"Updated literature landscape for project {project_id}")
        return project
    
    def update_hypothesis_set(self, project_id: str, hypothesis_set: HypothesisSet) -> ProjectState:
        """Update hypothesis set for a project.
        
        Args:
            project_id: Project identifier
            hypothesis_set: Generated hypotheses
            
        Returns:
            Updated ProjectState
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project.hypothesis_set = hypothesis_set
        project.update_status(ProjectStatus.HYPOTHESIS_GENERATION)
        self.save_project(project)
        logger.info(f"Updated hypothesis set for project {project_id}")
        return project
    
    def update_experiment_design(self, project_id: str, design: ExperimentDesign) -> ProjectState:
        """Update experiment design for a project.
        
        Args:
            project_id: Project identifier
            design: Experimental design
            
        Returns:
            Updated ProjectState
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project.experiment_design = design
        project.update_status(ProjectStatus.DESIGN_BUILDING)
        self.save_project(project)
        logger.info(f"Updated experiment design for project {project_id}")
        return project
    
    def update_stimulus_bank(self, project_id: str, stimulus_bank: StimulusBank) -> ProjectState:
        """Update stimulus bank for a project.
        
        Args:
            project_id: Project identifier
            stimulus_bank: Generated stimuli
            
        Returns:
            Updated ProjectState
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project.stimulus_bank = stimulus_bank
        project.update_status(ProjectStatus.STIMULUS_GENERATION)
        self.save_project(project)
        logger.info(f"Updated stimulus bank for project {project_id}")
        return project
    
    def update_simulation_results(self, project_id: str, results: SimulationResults) -> ProjectState:
        """Update simulation results for a project.
        
        Args:
            project_id: Project identifier
            results: Simulation results
            
        Returns:
            Updated ProjectState
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project.simulation_results = results
        project.update_status(ProjectStatus.SIMULATION)
        self.save_project(project)
        logger.info(f"Updated simulation results for project {project_id}")
        return project
    
    def create_checkpoint(self, project_id: str, checkpoint_name: str) -> None:
        """Create a checkpoint of current project state.
        
        Args:
            project_id: Project identifier
            checkpoint_name: Name for the checkpoint
        """
        project = self.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        checkpoint_file = self._get_checkpoint_file(project_id, checkpoint_name)
        with open(checkpoint_file, 'w') as f:
            json.dump(project.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Created checkpoint '{checkpoint_name}' for project {project_id}")
    
    def restore_checkpoint(self, project_id: str, checkpoint_name: str) -> ProjectState:
        """Restore project state from a checkpoint.
        
        Args:
            project_id: Project identifier
            checkpoint_name: Checkpoint to restore
            
        Returns:
            Restored ProjectState
        """
        checkpoint_file = self._get_checkpoint_file(project_id, checkpoint_name)
        if not checkpoint_file.exists():
            raise ValueError(f"Checkpoint '{checkpoint_name}' not found for project {project_id}")
        
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        project = ProjectState(**data)
        project.updated_at = datetime.utcnow()
        self.save_project(project)
        logger.info(f"Restored checkpoint '{checkpoint_name}' for project {project_id}")
        return project
    
    def list_checkpoints(self, project_id: str) -> List[str]:
        """List all checkpoints for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of checkpoint names
        """
        checkpoints_dir = self._get_project_dir(project_id) / "checkpoints"
        if not checkpoints_dir.exists():
            return []
        
        return [f.stem for f in checkpoints_dir.glob("*.json")]
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its data.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if deleted, False if not found
        """
        project_dir = self._get_project_dir(project_id)
        if not project_dir.exists():
            return False
        
        import shutil
        shutil.rmtree(project_dir)
        logger.info(f"Deleted project {project_id}")
        return True
