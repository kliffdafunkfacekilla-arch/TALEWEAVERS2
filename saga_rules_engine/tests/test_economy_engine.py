import unittest
from unittest.mock import patch
from saga_rules_engine.core.economy_engine import calculate_d_dust_rate

class TestEconomyEngine(unittest.TestCase):
    @patch('saga_rules_engine.core.economy_engine.random.uniform')
    def test_calculate_d_dust_rate_default(self, mock_uniform):
        # Default: base_rate=10.0, chaos_level=1
        # volatility = 0.2
        # min_swing = max(0.1, 1.0 - 0.2) = 0.8
        # max_swing = 1.0 + 0.2 = 1.2
        mock_uniform.return_value = 1.0  # mock a mid-point roll

        result = calculate_d_dust_rate()

        mock_uniform.assert_called_once_with(0.8, 1.2)
        self.assertEqual(result, 10.0)

    @patch('saga_rules_engine.core.economy_engine.random.uniform')
    def test_calculate_d_dust_rate_high_chaos(self, mock_uniform):
        # Chaos 6: base_rate=10.0, chaos_level=6
        # volatility = 1.2
        # min_swing = max(0.1, 1.0 - 1.2) = 0.1
        # max_swing = 1.0 + 1.2 = 2.2
        mock_uniform.return_value = 0.5

        result = calculate_d_dust_rate(chaos_level=6)

        mock_uniform.assert_called_once_with(0.1, 2.2)
        self.assertEqual(result, 5.0)

    @patch('saga_rules_engine.core.economy_engine.random.uniform')
    def test_calculate_d_dust_rate_no_chaos(self, mock_uniform):
        # Chaos 0: base_rate=10.0, chaos_level=0
        # volatility = 0.0
        # min_swing = 1.0
        # max_swing = 1.0
        mock_uniform.return_value = 1.0

        result = calculate_d_dust_rate(chaos_level=0)

        mock_uniform.assert_called_once_with(1.0, 1.0)
        self.assertEqual(result, 10.0)

    @patch('saga_rules_engine.core.economy_engine.random.uniform')
    def test_calculate_d_dust_rate_custom_base(self, mock_uniform):
        # Custom base 50.0, chaos_level=2
        # volatility = 0.4
        # min_swing = 0.6
        # max_swing = 1.4
        mock_uniform.return_value = 1.4

        result = calculate_d_dust_rate(base_rate=50.0, chaos_level=2)

        mock_uniform.assert_called_once_with(0.6, 1.4)
        self.assertEqual(result, 70.0)

if __name__ == '__main__':
    unittest.main()
