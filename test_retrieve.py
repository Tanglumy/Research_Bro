#!/usr/bin/env python3
import asyncio
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Load .env
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

from Literature_Landscape_Explorer.paper_retrieval import retrieve_papers

async def test():
    print('\n=== Testing retrieve_papers ===')
    try:
        result = await retrieve_papers(['attachment anxiety'], limit=5)
        print(f'\nRESULT: {len(result)} papers')
        if result:
            for i, p in enumerate(result[:3], 1):
                print(f'  {i}. {p.title}')
        else:
            print('  No papers returned')
    except Exception as e:
        print(f'\nERROR: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test())
