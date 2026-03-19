import sys
import unittest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add saga_character_engine to sys.path so we can import core
sys.path.append(str(Path(__file__).resolve().parent))

from core.storage import save_character, load_character

class TestStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Patch CHAR_DATA_DIR in the storage module to point to our temp directory
        self.patcher = patch('core.storage.CHAR_DATA_DIR', self.temp_path)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_save_and_load_character_success(self):
        player_id = "test_player_1"
        sheet_data = {"name": "Test Character", "level": 5, "attributes": {"str": 10}}

        # Save should succeed
        success = save_character(player_id, sheet_data)
        self.assertTrue(success)

        # Check if file actually exists
        expected_path = self.temp_path / f"{player_id}.json"
        self.assertTrue(expected_path.exists())

        # Load should return the exact same dictionary
        loaded_data = load_character(player_id)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data, sheet_data)

    def test_load_character_not_found(self):
        player_id = "non_existent_player"

        # Load should return None if file doesn't exist
        loaded_data = load_character(player_id)
        self.assertIsNone(loaded_data)

    @patch('core.storage.os.makedirs')
    def test_save_character_error(self, mock_makedirs):
        player_id = "error_player"
        sheet_data = {"name": "Error Character"}

        # Force an exception during os.makedirs
        mock_makedirs.side_effect = PermissionError("Permission denied")

        # Save should catch the exception and return False
        success = save_character(player_id, sheet_data)
        self.assertFalse(success)

    def test_load_character_error(self):
        player_id = "corrupted_player"
        sheet_data = "This is not valid JSON"

        # First write invalid JSON manually
        file_path = self.temp_path / f"{player_id}.json"
        with open(file_path, 'w') as f:
            f.write(sheet_data)

        # Load should fail parsing JSON, catch the exception, and return None
        loaded_data = load_character(player_id)
        self.assertIsNone(loaded_data)

if __name__ == '__main__':
    unittest.main()
