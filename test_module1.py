import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from copilot_workflow.schemas import ProjectState, ResearchQuestion
from Literature_Landscape_Explorer.run import run_with_summary

async def test():
    project = ProjectState()
    project.rq = ResearchQuestion(
        raw_text='How does attachment anxiety influence emotion regulation?',
        parsed_constructs=['attachment anxiety', 'emotion regulation'],
        domain='Psychology'
    )
    
    result, summary = await run_with_summary(project)
    
    print(f'\nPapers in summary: {summary.get("papers", 0)}')
    print(f'\nAudit log entries:')
    for e in result.audit_log:
        print(f'  [{e.level}] {e.location}: {e.message}')

asyncio.run(test())
