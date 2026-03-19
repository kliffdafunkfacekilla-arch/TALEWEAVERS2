import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio

# Setup mocks before importing anything from saga_director
fastapi_mock = MagicMock()
sys.modules["fastapi"] = fastapi_mock
sys.modules["fastapi.responses"] = MagicMock()
sys.modules["fastapi.middleware.cors"] = MagicMock()
sys.modules["pydantic"] = MagicMock()
sys.modules["sqlalchemy"] = MagicMock()
sys.modules["sqlalchemy.orm"] = MagicMock()
sys.modules["sqlalchemy.ext.declarative"] = MagicMock()
sys.modules["httpx"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.spatial"] = MagicMock()
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.llms"] = MagicMock()
sys.modules["langchain.prompts"] = MagicMock()
sys.modules["langchain.chains"] = MagicMock()
sys.modules["networkx"] = MagicMock()

# Mock internal modules
sys.modules["core"] = MagicMock()
sys.modules["core.ai_narrator"] = MagicMock()
sys.modules["core.ai_narrator.graph"] = MagicMock()
sys.modules["core.ai_narrator.state"] = MagicMock()
sys.modules["core.models"] = MagicMock()
sys.modules["core.api_gateway"] = MagicMock()
sys.modules["core.context"] = MagicMock()
sys.modules["core.tactical_generator"] = MagicMock()
sys.modules["core.pathfinder"] = MagicMock()
sys.modules["core.world_manager"] = MagicMock()
sys.modules["core.database"] = MagicMock()
sys.modules["core.weaver_schemas"] = MagicMock()
sys.modules["core.weaver"] = MagicMock()
sys.modules["core.encounter_schemas"] = MagicMock()
sys.modules["core.generator"] = MagicMock()

# Add saga_director to path
sys.path.append(os.path.join(os.getcwd(), "saga_director"))

# We need to ensure @app.post and @app.get don't return Mocks that hide the actual functions
def mock_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

fastapi_mock.FastAPI.return_value.post = mock_decorator
fastapi_mock.FastAPI.return_value.get = mock_decorator

# Import main directly from the file
import saga_director.main as main

class TestEncounterArgs(unittest.TestCase):

    @patch("saga_director.main.api_gateway.generate_campaign_framework", new_callable=AsyncMock)
    @patch("saga_director.main.ContextAssembler")
    @patch("saga_director.main.TacticalGenerator.generate_ambient_encounter")
    @patch("saga_director.main.process_chat_action_internal", new_callable=AsyncMock)
    @patch("saga_director.main.SessionLocal")
    @patch("saga_director.main.CampaignState")
    @patch("saga_director.main.CampaignFrameworkTable")
    @patch("saga_director.main.ActiveQuest")
    def test_start_campaign_args(self, mock_quest, mock_framework_table, mock_campaign_state, mock_session, mock_chat, mock_gen_encounter, mock_assembler, mock_framework):
        # Setup mocks
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_framework.return_value = {"hero_journey": [{"title": "Test Beat"}]}

        mock_assembler_inst = MagicMock()
        mock_assembler_inst.assemble = AsyncMock(return_value={"location": {"biome": "Tundra"}, "active_npcs": [{"name": "Mock NPC"}]})
        mock_assembler.return_value = mock_assembler_inst

        mock_gen_encounter.return_value = {"encounter_id": "test"}

        mock_chat.return_value = {"narration": "test", "active_encounter": {}}

        request = MagicMock()
        request.player_id = "test_player"
        request.starting_hex_id = 402
        request.composite_sprite = {"head": "helmet"}
        request.length = "SAGA"
        request.difficulty = "STANDARD"
        request.style = "GRITTY_SURVIVAL"
        request.no_fly_list = []
        request.world_id = "W_001"

        asyncio.run(main.start_campaign(request))

        # Verify TacticalGenerator.generate_ambient_encounter call
        mock_gen_encounter.assert_called_once()
        args, kwargs = mock_gen_encounter.call_args
        self.assertEqual(args[0], "Tundra") # biome
        self.assertEqual(args[1], 402) # hex_id
        self.assertEqual(kwargs["active_npcs"], [{"name": "Mock NPC"}])
        self.assertEqual(kwargs["player_sprite"], {"head": "helmet"})

    @patch("saga_director.main.SessionLocal")
    @patch("saga_director.main.ContextAssembler")
    @patch("saga_director.main.TacticalGenerator.generate_ambient_encounter")
    def test_get_tactical_grid_args(self, mock_gen_encounter, mock_assembler, mock_session):
        # Setup mocks
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_state = MagicMock()
        mock_state.day_phase = "EVENING"
        mock_state.hex_densities = {"500": {"wolf": 0.5}}
        mock_state.player_sprite = {"body": "armor"}
        mock_db.query().filter().first.return_value = mock_state

        mock_assembler_inst = MagicMock()
        mock_assembler_inst.assemble = AsyncMock(return_value={"location": {"biome": "Swamp"}, "active_npcs": [{"name": "Swamp NPC"}]})
        mock_assembler.return_value = mock_assembler_inst

        mock_gen_encounter.return_value = {"encounter_id": "test_tactical"}

        asyncio.run(main.get_tactical_grid(500, 10, 20, campaign_id="test_camp"))

        # Verify TacticalGenerator.generate_ambient_encounter call
        mock_gen_encounter.assert_called_once()
        args, kwargs = mock_gen_encounter.call_args
        self.assertEqual(args[0], "Swamp") # biome
        self.assertEqual(args[1], 500) # hex_id
        self.assertEqual(args[2], 10) # lx
        self.assertEqual(args[3], 20) # ly
        self.assertEqual(kwargs["current_hour"], 19.0) # EVENING
        self.assertEqual(kwargs["densities"], {"wolf": 0.5})
        self.assertEqual(kwargs["active_npcs"], [{"name": "Swamp NPC"}])
        self.assertEqual(kwargs["player_sprite"], {"body": "armor"})

if __name__ == "__main__":
    unittest.main()
