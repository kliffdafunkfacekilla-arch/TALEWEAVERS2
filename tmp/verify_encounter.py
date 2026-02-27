import asyncio
import httpx
import json
import traceback

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
            print("Calling /action (MOVE)...")
            res1 = await client.post("http://localhost:8000/action", json=payload_move, timeout=90.0)
            if res1.status_code != 200:
                print(f"Server Error {res1.status_code}: {res1.text}")
                return
                
            update1 = res1.json()
            print(f"Narrator (HTML): {update1.get('ai_narration_html')[:100]}...")
            
            enc = update1.get("active_encounter")
            if not enc:
                print("No encounter triggered in this move.")
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
                
                print(f"Calling /action (PERSUADE) on {npc_name}...")
                res2 = await client.post("http://localhost:8000/action", json=payload_talk, timeout=90.0)
                if res2.status_code != 200:
                    print(f"Server Error {res2.status_code}: {res2.text}")
                    return
                    
                update2 = res2.json()
                print(f"System Log: {update2.get('system_log')}")
                print(f"Narrator (HTML): {update2.get('ai_narration_html')[:100]}...")
                
            else:
                print(f"Encounter is {enc['data'].get('category')}, skipping PERSUADE test.")

        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_silver_tongue_loop())
