import asyncio
import httpx
import json

async def test_silver_tongue_loop():
    print("--- STEP 1: MOVE TO TRIGGER ENCOUNTER ---")
    payload_move = {
        "player_id": "char_001",
        "action_type": "MOVE",
        "action_target": "[10, 15]",
        "raw_chat_text": "I enter the village square.",
        "stamina_burned": 1
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. Trigger the Encounter
            res1 = await client.post("http://localhost:8000/action", json=payload_move, timeout=20.0)
            res1.raise_for_status()
            update1 = res1.json()
            
            print(f"Narrator: {update1.get('ai_narration_html')}")
            enc = update1.get("active_encounter")
            
            if not enc:
                print("No encounter triggered. (Random chance or seed issue)")
                return

            print(f"\nENCOUNTER DETECTED: {enc['data']['title']} ({enc['data'].get('category')})")

            # 2. Simulate PERSUADE (Social Combat)
            if enc['data'].get('category') == 'SOCIAL':
                print("\n--- STEP 2: SIMULATING PERSUADE ACTION ---")
                npc_name = enc['data']['npcs'][0]['name']
                payload_talk = {
                    "player_id": "char_001",
                    "action_type": "PERSUADE",
                    "action_target": npc_name,
                    "raw_chat_text": "Listen to reason, my friend.",
                    "stamina_burned": 2
                }
                
                res2 = await client.post("http://localhost:8000/action", json=payload_talk, timeout=20.0)
                res2.raise_for_status()
                update2 = res2.json()
                
                print(f"System Log: {update2.get('system_log')}")
                print(f"Narrator: {update2.get('ai_narration_html')}")
                
            elif enc['data'].get('category') == 'HAZARD':
                 print("\n--- STEP 2: SIMULATING DISARM ACTION ---")
                 payload_disarm = {
                    "player_id": "char_001",
                    "action_type": "DISARM",
                    "action_target": enc['data']['title'],
                    "stamina_burned": 2
                }
                 res2 = await client.post("http://localhost:8000/action", json=payload_disarm, timeout=20.0)
                 res2.raise_for_status()
                 update2 = res2.json()
                 print(f"System Log: {update2.get('system_log')}")

        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_silver_tongue_loop())
