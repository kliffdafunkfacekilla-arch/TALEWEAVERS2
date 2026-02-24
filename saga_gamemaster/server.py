from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from saga_gamemaster.core.vtt_schemas import PlayerAction, VTTUpdate
from saga_gamemaster.core.database import get_session, init_db
from saga_gamemaster.core.ai_narrator.graph import create_director_graph
from saga_gamemaster.core.ai_narrator.state import GameState
import uvicorn

app = FastAPI(title="SAGA Core GM App", port=8000)

director_graph = create_director_graph()

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/action", response_model=VTTUpdate)
async def handle_player_action(action: PlayerAction, db: AsyncSession = Depends(get_session)):
    # 1. Initialize State
    initial_state: GameState = {
        "player_id": action.player_id,
        "action_type": action.action_type,
        "action_target": action.action_target,
        "raw_chat_text": action.raw_chat_text,
        "stamina_burned": action.stamina_burned,
        "current_location": "",
        "active_quests": [],
        "player_vitals": {},
        "math_log": "",
        "director_override": None,
        "vtt_commands": [],
        "ai_narration": ""
    }
    
    # 2. Run LangGraph Workflow
    try:
        final_state = await director_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 3. Construct VTT Update
    # In a real scenario, we would also update the Database here
    # (e.g., updating player vitals, quests, etc.)
    
    response = VTTUpdate(
        ai_narration_html=f"<div>{final_state['ai_narration']}</div>",
        system_log=final_state["math_log"],
        ui_refresh_required=True if final_state["math_log"] else False,
        vtt_commands=final_state["vtt_commands"]
    )
    
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
