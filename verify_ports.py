import httpx
import asyncio
import sys

services = [
    ("Lore Vault", "http://localhost:8001/"),
    ("World Architect", "http://localhost:8002/api/world/current"), # Check if generated
    ("Character Engine", "http://localhost:8003/"),
    ("Encounter Engine", "http://localhost:8004/"),
    ("Item Foundry", "http://localhost:8005/"),
    ("Skill Engine", "http://localhost:8006/"),
    ("Clash Engine", "http://localhost:8007/"),
    ("Tactical Magic", "http://localhost:8008/"),
    ("Saga Director", "http://localhost:8000/"),
    ("Campaign Weaver", "http://localhost:8010/"),
    ("Asset Foundry", "http://localhost:8012/api/assets/map/object/barrel"),
    ("Chronos Engine", "http://localhost:9000/health"),
]

async def check_service(name, url):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # We use GET/POST depending on endpoint, but a simple head or get for health is usually enough
            response = await client.get(url)
            if response.status_code in [200, 404, 405]: # 404/405 means it's running but we hit a specific endpoint wrong
                print(f"[OK] {name} is reachable at {url}")
                return True
            else:
                print(f"[FAIL] {name} at {url} returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"[OFFLINE] {name} is unreachable at {url}. Error: {type(e).__name__}")
        return False

async def main():
    print("========================================")
    print("T.A.L.E.W.E.A.V.E.R. Port Verification")
    print("========================================\n")
    
    results = await asyncio.gather(*(check_service(name, url) for name, url in services))
    
    print("\n----------------------------------------")
    if all(results):
        print("SUCCESS: All services are correctly mapped and reachable!")
    else:
        print("WARNING: Some services are offline. Start them with run_all.bat before playing.")
    print("----------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
