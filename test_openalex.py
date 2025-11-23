import asyncio
import httpx

async def test_openalex():
    url = "https://api.openalex.org/works"
    params = {
        "search": "attachment anxiety",
        "per_page": 5,
        "filter": "type:article",
        "mailto": "contact@sylph.ai"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        results = data.get("results", [])
        print(f"Results: {len(results)}")
        for i, work in enumerate(results[:3], 1):
            print(f"  {i}. {work.get('display_name', 'N/A')}")

asyncio.run(test_openalex())
