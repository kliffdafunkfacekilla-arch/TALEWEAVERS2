import unittest
from unittest.mock import patch
from saga_rules_engine.core.clash_calculator import roll_dice, resolve_clash, roll_d20
from saga_rules_engine.core.clash_schemas import ClashRequest, ClashResolution
from saga_common.models.core import CombatantState

class TestClashCalculator(unittest.TestCase):
    def setUp(self):
        self.attacker = CombatantState(
            name="Attacker",
            skill_rank=2, # rank bonus = 2 // 2 = 1
            stat_mod=3,
            weapon_damage_dice="1d8"
        ) # Total bonus = 2 + 3 + 1 = 6

        self.defender = CombatantState(
            name="Defender",
            skill_rank=2, # rank bonus = 2 // 2 = 1
            stat_mod=2,
            weapon_damage_dice="1d6"
        ) # Total bonus = 2 + 2 + 1 = 5

    @patch('saga_rules_engine.core.clash_calculator.random.randint')
    def test_roll_dice_standard(self, mock_randint):
        mock_randint.side_effect = [5, 4]  # Example rolls for 2d6
        result = roll_dice("2d6")
        self.assertEqual(result, 9)

    @patch('saga_rules_engine.core.clash_calculator.random.randint')
    def test_roll_dice_with_positive_bonus(self, mock_randint):
        mock_randint.side_effect = [8]  # Example roll for 1d8
        result = roll_dice("1d8+2")
        self.assertEqual(result, 10)

    @patch('saga_rules_engine.core.clash_calculator.random.randint')
    def test_roll_dice_with_negative_bonus(self, mock_randint):
        mock_randint.side_effect = [3]  # Example roll for 1d6
        result = roll_dice("1d6-1")
        self.assertEqual(result, 2)

    def test_roll_dice_flat_number(self):
        result = roll_dice("5")
        self.assertEqual(result, 5)

    def test_roll_dice_empty_or_invalid(self):
        self.assertEqual(roll_dice(""), 0)
        self.assertEqual(roll_dice(None), 0)
        self.assertEqual(roll_dice("invalid"), 0)

    @patch('saga_rules_engine.core.clash_calculator.roll_dice')
    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_critical_hit(self, mock_d20, mock_roll_dice):
        # margin >= 10
        # attacker total = d20 + 6
        # defender total = d20 + 5
        mock_d20.side_effect = [14, 5] # 14 + 6 = 20, 5 + 5 = 10 -> margin 10 # 18 + 6 = 24, 5 + 5 = 10 -> margin 14
        mock_roll_dice.return_value = 5 # damage

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "CRITICAL_HIT")
        self.assertEqual(res.margin, 10)
        self.assertEqual(res.defender_hp_change, -10) # damage * 2

    @patch('saga_rules_engine.core.clash_calculator.roll_dice')
    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_normal_hit_upper_bound(self, mock_d20, mock_roll_dice):
        # 4 <= margin <= 9 -> test 9
        mock_d20.side_effect = [15, 7] # 15 + 6 = 21, 7 + 5 = 12 -> margin 9
        mock_roll_dice.return_value = 5

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "NORMAL_HIT")
        self.assertEqual(res.margin, 9)
        self.assertEqual(res.defender_hp_change, -5)

    @patch('saga_rules_engine.core.clash_calculator.roll_dice')
    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_normal_hit_lower_bound(self, mock_d20, mock_roll_dice):
        # 4 <= margin <= 9 -> test 4
        mock_d20.side_effect = [10, 7] # 10 + 6 = 16, 7 + 5 = 12 -> margin 4
        mock_roll_dice.return_value = 5

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "NORMAL_HIT")
        self.assertEqual(res.margin, 4)
        self.assertEqual(res.defender_hp_change, -5)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_graze_upper_bound(self, mock_d20):
        # 1 <= margin <= 3 -> test 3
        mock_d20.side_effect = [10, 8] # 10 + 6 = 16, 8 + 5 = 13 -> margin 3

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "GRAZE")
        self.assertEqual(res.margin, 3)
        self.assertEqual(res.defender_composure_change, -1)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_graze_lower_bound(self, mock_d20):
        # 1 <= margin <= 3 -> test 1
        mock_d20.side_effect = [10, 10] # 10 + 6 = 16, 10 + 5 = 15 -> margin 1

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "GRAZE")
        self.assertEqual(res.margin, 1)
        self.assertEqual(res.defender_composure_change, -1)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_tie(self, mock_d20):
        # margin == 0
        mock_d20.side_effect = [10, 11] # 10 + 6 = 16, 11 + 5 = 16 -> margin 0

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "CLASH_TIE")
        self.assertEqual(res.margin, 0)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_defensive_success_upper_bound(self, mock_d20):
        # -5 <= margin <= -1 -> test -1
        mock_d20.side_effect = [10, 12] # 10 + 6 = 16, 12 + 5 = 17 -> margin -1

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "DEFENSIVE_SUCCESS")
        self.assertEqual(res.margin, -1)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_defensive_success_lower_bound(self, mock_d20):
        # -5 <= margin <= -1 -> test -5
        mock_d20.side_effect = [10, 16] # 10 + 6 = 16, 16 + 5 = 21 -> margin -5

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "DEFENSIVE_SUCCESS")
        self.assertEqual(res.margin, -5)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_rattling_defense_upper_bound(self, mock_d20):
        # -11 <= margin <= -6 -> test -6
        mock_d20.side_effect = [10, 17] # 10 + 6 = 16, 17 + 5 = 22 -> margin -6

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "RATTLING_DEFENSE")
        self.assertEqual(res.margin, -6)
        self.assertEqual(res.attacker_composure_change, -1)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_rattling_defense_lower_bound(self, mock_d20):
        # -11 <= margin <= -6 -> test -11
        mock_d20.side_effect = [5, 17] # 5 + 6 = 11, 17 + 5 = 22 -> margin -11

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "RATTLING_DEFENSE")
        self.assertEqual(res.margin, -11)
        self.assertEqual(res.attacker_composure_change, -1)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_critical_miss(self, mock_d20):
        # margin < -11 -> test -12
        mock_d20.side_effect = [5, 18] # 5 + 6 = 11, 18 + 5 = 23 -> margin -12

        req = ClashRequest(attacker=self.attacker, defender=self.defender)
        res = resolve_clash(req)

        self.assertEqual(res.clash_result, "CRITICAL_MISS")
        self.assertEqual(res.margin, -12)
        self.assertEqual(res.chaos_effect_triggered, "Attacker falls PRONE.")

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_attacker_advantage(self, mock_d20):
        # attacker rolls 2, 10 -> takes 10
        # defender rolls 5 -> takes 5
        mock_d20.side_effect = [2, 10, 5]

        req = ClashRequest(
            attacker=self.attacker,
            defender=self.defender,
            attacker_advantage=True
        )
        res = resolve_clash(req)

        # Attacker total: 10 + 6 = 16
        # Defender total: 5 + 5 = 10
        # Margin: 6
        self.assertEqual(res.attacker_roll, 16)
        self.assertEqual(res.defender_roll, 10)
        self.assertEqual(res.margin, 6)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_attacker_disadvantage(self, mock_d20):
        # attacker rolls 10, 2 -> takes 2
        # defender rolls 5 -> takes 5
        mock_d20.side_effect = [10, 2, 5]

        req = ClashRequest(
            attacker=self.attacker,
            defender=self.defender,
            attacker_disadvantage=True
        )
        res = resolve_clash(req)

        # Attacker total: 2 + 6 = 8
        # Defender total: 5 + 5 = 10
        # Margin: -2
        self.assertEqual(res.attacker_roll, 8)
        self.assertEqual(res.defender_roll, 10)
        self.assertEqual(res.margin, -2)

    @patch('saga_rules_engine.core.clash_calculator.roll_d20')
    def test_resolve_clash_defender_advantage_and_disadvantage_cancel(self, mock_d20):
        # If both are true, roll_with_benefit returns base_roll_func()
        # attacker rolls 10 -> takes 10
        # defender rolls 15, 20 -> should just roll once, so takes 15
        # actually, roll_with_benefit only calls once if both are True!
        mock_d20.side_effect = [10, 15]

        req = ClashRequest(
            attacker=self.attacker,
            defender=self.defender,
            defender_advantage=True,
            defender_disadvantage=True
        )
        res = resolve_clash(req)

        # Attacker total: 10 + 6 = 16
        # Defender total: 15 + 5 = 20
        # Margin: -4
        self.assertEqual(res.attacker_roll, 16)
        self.assertEqual(res.defender_roll, 20)
        self.assertEqual(res.margin, -4)

if __name__ == '__main__':
    unittest.main()
