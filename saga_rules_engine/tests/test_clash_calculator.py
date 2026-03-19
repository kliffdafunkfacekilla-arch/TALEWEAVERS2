import unittest
from unittest.mock import patch
from saga_rules_engine.core.clash_calculator import roll_dice

class TestClashCalculator(unittest.TestCase):
    def test_roll_dice_valid(self):
        """Test valid dice strings like '1d8+2' and '2d6-1' fall within expected ranges."""
        for _ in range(20):
            res_add = roll_dice("1d8+2")
            self.assertTrue(3 <= res_add <= 10, f"Expected 3-10, got {res_add}")

            res_sub = roll_dice("2d6-1")
            self.assertTrue(1 <= res_sub <= 11, f"Expected 1-11, got {res_sub}")

            res_plain = roll_dice("3d4")
            self.assertTrue(3 <= res_plain <= 12, f"Expected 3-12, got {res_plain}")

    def test_roll_dice_empty_string(self):
        """Test empty string and None return 0."""
        self.assertEqual(roll_dice(""), 0)
        self.assertEqual(roll_dice(None), 0)

    def test_roll_dice_constant_number(self):
        """Test strings that are just integers parse correctly."""
        self.assertEqual(roll_dice("5"), 5)
        self.assertEqual(roll_dice("-3"), -3)

    def test_roll_dice_error_paths(self):
        """Test unparseable strings trigger the exception block and return 0."""
        self.assertEqual(roll_dice("ad8"), 0)  # Cannot parse number of dice
        self.assertEqual(roll_dice("1da"), 0)  # Cannot parse number of sides
        self.assertEqual(roll_dice("1d8+a"), 0) # Cannot parse bonus
        self.assertEqual(roll_dice("hello"), 0) # Cannot parse constant

    @patch("saga_rules_engine.core.clash_calculator.random.randint")
    def test_roll_dice_exception(self, mock_randint):
        """Explicitly test the broad exception catch by forcing an Exception inside the valid path."""
        mock_randint.side_effect = Exception("Mocked unexpected error")
        self.assertEqual(roll_dice("1d8"), 0)

if __name__ == '__main__':
    unittest.main()
