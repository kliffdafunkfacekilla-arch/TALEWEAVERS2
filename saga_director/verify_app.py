import httpx
import asyncio
import json

async def test_action():
    url = "http://localhost:8000/action"
    
    # 1. Test MOVE action (Triggers Director Override if [10, 15])
    move_action = {
        "player_id": "player_123",
        "action_type": "MOVE",
        "action_target": "[10, 15]",
        "raw_chat_text": "I head towards the glowing light.",
        "stamina_burned": 2
    }
    
    print("Testing MOVE action to [10, 15] (Ambush Trigger)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=move_action, timeout=10.0)
            print(f"Status: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")

    # 2. Test ATTACK action
    attack_action = {
        "player_id": "player_123",
        "action_type": "ATTACK",
        "action_target": "NPC_Wolf_01",
        "raw_chat_text": "I strike with my axe!",
        "stamina_burned": 5
    }
    
    print("\nTesting ATTACK action...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=attack_action, timeout=10.0)
            print(f"Status: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_action())
