import unittest
import random
from saga_item_engine.core.effect_resolver import parse_dice

class TestDiceParsing(unittest.TestCase):
    def test_basic_dice(self):
        """Test simple dice notation like 1d4, 2d6."""
        for _ in range(100):
            result = parse_dice("1d4")
            self.assertTrue(1 <= result <= 4, f"1d4 roll resulted in {result}")

            result = parse_dice("2d6")
            self.assertTrue(2 <= result <= 12, f"2d6 roll resulted in {result}")

    def test_dice_with_modifier(self):
        """Test dice with positive and negative modifiers."""
        for _ in range(100):
            result = parse_dice("1d8+2")
            self.assertTrue(3 <= result <= 10, f"1d8+2 roll resulted in {result}")

            result = parse_dice("1d8-1")
            self.assertTrue(1 <= result <= 7, f"1d8-1 roll resulted in {result}")

    def test_whitespace_and_case(self):
        """Test that whitespace and case don't affect parsing."""
        res = parse_dice(" 1D4 ")
        self.assertTrue(1 <= res <= 4, f"1D4 roll resulted in {res}")

        res = parse_dice("2 d 6 + 2")
        self.assertTrue(4 <= res <= 14, f"2 d 6 + 2 roll resulted in {res}")

    def test_invalid_inputs(self):
        """Test that invalid strings return 0 safely."""
        self.assertEqual(parse_dice("invalid"), 0)
        self.assertEqual(parse_dice("2d"), 0)
        self.assertEqual(parse_dice("d6"), 0)
        self.assertEqual(parse_dice(""), 0)
        self.assertEqual(parse_dice("10"), 0)

    def test_edge_cases(self):
        """Test edge cases like zero dice."""
        # Current implementation: 0d6 -> match found, but num_dice=0, roll_total=0.
        # Returns max(1, 0) = 1.
        self.assertEqual(parse_dice("0d6"), 1)

    def test_zero_sides(self):
        """Test that 1d0 doesn't crash and returns at least 1."""
        result = parse_dice("1d0")
        self.assertEqual(result, 1)

    def test_minimum_result(self):
        """Test that result never goes below 1 if it's a valid dice string."""
        self.assertEqual(parse_dice("1d4-10"), 1)

    def test_unusual_patterns(self):
        """Test strings with extra text but containing dice patterns."""
        self.assertTrue(1 <= parse_dice("I roll 1d4 for damage") <= 4)
        self.assertTrue(1 <= parse_dice("1d6 damage + 1d4 healing") <= 6)

if __name__ == "__main__":
    unittest.main()
