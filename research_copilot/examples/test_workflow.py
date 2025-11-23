#!/usr/bin/env python3
"""Example script demonstrating Research Copilot workflow.

This script shows how to use the Research Copilot backend service
to execute a complete research workflow from idea to literature landscape.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from spoon_ai.llm import LLMManager, ConfigurationManager
from spoon_ai.research_copilot import (
    ProjectStateService,
    LiteratureExplorer,
    ProjectState
)


async def main():
    """Run example research workflow."""
    print("="*60)
    print("Research Copilot - Example Workflow")
    print("="*60)
    print()
    
    # Initialize services
    print("[1/5] Initializing services...")
    llm_manager = LLMManager(ConfigurationManager())
    state_service = ProjectStateService(storage_dir="./research_projects")
    explorer = LiteratureExplorer(llm_manager)
    print("✓ Services initialized")
    print()
    
    # Create a new project
    print("[2/5] Creating project...")
    project_name = "Attachment Anxiety and Emotion Regulation Study"
    research_question = (
        "How does attachment anxiety influence emotion regulation strategies "
        "in romantic relationships, and what role does self-compassion play?"
    )
    
    project = state_service.create_project(
        name=project_name,
        research_question_text=research_question
    )
    
    print(f"✓ Project created: {project.id}")
    print(f"  Name: {project.name}")
    print(f"  Question: {project.research_question.raw_text}")
    print()
    
    # Run literature exploration
    print("[3/5] Running literature exploration...")
    print("  (This may take 30-60 seconds)")
    
    try:
        landscape = await explorer.explore(project.research_question)
        print("✓ Literature exploration completed")
        print()
        
        # Display results
        print("[4/5] Results summary:")
        print(f"  Constructs identified: {len(project.research_question.parsed_constructs)}")
        for i, construct in enumerate(project.research_question.parsed_constructs, 1):
            print(f"    {i}. {construct}")
        print()
        
        print(f"  Knowledge graph:")
        print(f"    - Nodes: {len(landscape.knowledge_graph.nodes)}")
        print(f"    - Edges: {len(landscape.knowledge_graph.edges)}")
        print()
        
        print(f"  Theoretical frameworks: {len(landscape.theoretical_frameworks)}")
        for framework in landscape.theoretical_frameworks:
            print(f"    - {framework.get('name', 'Unknown')}")
        print()
        
        print(f"  Common measures:")
        for construct, measures in list(landscape.common_measures.items())[:3]:
            print(f"    {construct}: {', '.join(measures[:3])}")
        print()
        
        print(f"  Research gaps identified:")
        print(f"    {landscape.gaps.description}")
        if landscape.gaps.missing_combinations:
            print(f"    - Missing combinations: {len(landscape.gaps.missing_combinations)}")
        if landscape.gaps.unexplored_populations:
            print(f"    - Unexplored populations: {', '.join(landscape.gaps.unexplored_populations[:2])}")
        print()
        
        print(f"  Citations collected: {len(landscape.citations)}")
        print()
        
        # Update project state
        print("[5/5] Saving results...")
        project = state_service.update_literature_landscape(project.id, landscape)
        print(f"✓ Project state updated")
        print(f"  Status: {project.status.value}")
        print()
        
        # Create checkpoint
        state_service.create_checkpoint(project.id, "after-literature-exploration")
        print("✓ Checkpoint created: 'after-literature-exploration'")
        print()
        
        # Display next steps
        print("="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Review the literature landscape in:")
        print(f"   research_projects/{project.id}/state.json")
        print()
        print("2. Run hypothesis generation (when implemented):")
        print("   POST /api/workflow/hypothesis-engine")
        print()
        print("3. View project in API:")
        print(f"   GET http://localhost:8000/api/projects/{project.id}")
        print()
        print("4. Restore from checkpoint if needed:")
        print(f"   POST /api/projects/{project.id}/checkpoints/after-literature-exploration/restore")
        print()
        
    except Exception as e:
        print(f"✗ Error during literature exploration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("="*60)
    print("Workflow completed successfully!")
    print("="*60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
