import unittest
from saga_rules_engine.core.schemas import CoreAttributes, DerivedVitals
from saga_rules_engine.core.calc_vitals import calculate_pools

class TestCalcVitals(unittest.TestCase):
    def test_calculate_pools_standard(self):
        stats = CoreAttributes(
            might=5, reflexes=5, vitality=5,
            endurance=4, fortitude=4, finesse=4,
            willpower=3, logic=3, awareness=3,
            knowledge=2, charm=2, intuition=2
        )
        vitals = calculate_pools(stats)

        self.assertIsInstance(vitals, DerivedVitals)
        self.assertEqual(vitals.max_hp, 15) # 5 + 5 + 5
        self.assertEqual(vitals.max_stamina, 12) # 4 + 4 + 4
        self.assertEqual(vitals.max_composure, 9) # 3 + 3 + 3
        self.assertEqual(vitals.max_focus, 6) # 2 + 2 + 2

    def test_calculate_pools_zeroes(self):
        stats = CoreAttributes() # defaults are 0
        vitals = calculate_pools(stats)

        self.assertEqual(vitals.max_hp, 0)
        self.assertEqual(vitals.max_stamina, 0)
        self.assertEqual(vitals.max_composure, 0)
        self.assertEqual(vitals.max_focus, 0)

    def test_calculate_pools_large_values(self):
        stats = CoreAttributes(
            might=100, reflexes=100, vitality=100,
            endurance=100, fortitude=100, finesse=100,
            willpower=100, logic=100, awareness=100,
            knowledge=100, charm=100, intuition=100
        )
        vitals = calculate_pools(stats)

        self.assertEqual(vitals.max_hp, 300)
        self.assertEqual(vitals.max_stamina, 300)
        self.assertEqual(vitals.max_composure, 300)
        self.assertEqual(vitals.max_focus, 300)

    def test_calculate_pools_negative_values(self):
        # Even if not practically possible, the math logic should hold
        stats = CoreAttributes(
            might=-1, reflexes=-2, vitality=-3,
            endurance=-4, fortitude=-5, finesse=-6,
            willpower=-7, logic=-8, awareness=-9,
            knowledge=-10, charm=-11, intuition=-12
        )
        vitals = calculate_pools(stats)

        self.assertEqual(vitals.max_hp, -6)
        self.assertEqual(vitals.max_stamina, -15)
        self.assertEqual(vitals.max_composure, -24)
        self.assertEqual(vitals.max_focus, -33)

if __name__ == '__main__':
    unittest.main()
