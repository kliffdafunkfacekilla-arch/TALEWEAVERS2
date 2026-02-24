from core.economy_engine import calculate_d_dust_rate
from core.effect_resolver import resolve_consumable, parse_dice
from core.data_loader import load_item_by_id

def test_dice_parsing():
    print("Testing dice parsing...")
    assert 1 <= parse_dice("1d4") <= 4
    assert 2 <= parse_dice("2d6") <= 12
    print("Dice parsing tests passed!")

def test_economy_volatility():
    print("\nTesting economy volatility...")
    base_rate = 10.0
    chaos_1 = [calculate_d_dust_rate(base_rate, 1) for _ in range(100)]
    chaos_5 = [calculate_d_dust_rate(base_rate, 5) for _ in range(100)]
    
    # Chaos 1 volatility is 0.2, so range should be [8.0, 12.0]
    assert all(8.0 <= r <= 12.0 for r in chaos_1)
    
    # Chaos 5 volatility is 1.0, so range should be [0.0, 20.0]
    assert all(0.0 <= r <= 20.0 for r in chaos_5)
    
    print(f"Chaos 1 sample: {chaos_1[:5]}")
    print(f"Chaos 5 sample: {chaos_5[:5]}")
    print("Economy volatility tests passed!")

def test_consumable_resolution():
    print("\nTesting consumable resolution...")
    vigor_salts = load_item_by_id("VIGOR_SALTS")
    cinder_pot = load_item_by_id("CINDER_POT")
    
    assert vigor_salts is not None
    assert cinder_pot is not None
    
    res_v = resolve_consumable(vigor_salts, {})
    assert res_v["action"] == "HEAL"
    assert res_v["target_pool"] == "Stamina"
    assert 1 <= res_v["math_result"] <= 4
    
    res_c = resolve_consumable(cinder_pot, {})
    assert res_c["action"] == "DAMAGE"
    assert 2 <= res_c["math_result"] <= 12
    
    print(f"Vigor Salts result: {res_v}")
    print(f"Cinder Pot result: {res_c}")
    print("Consumable resolution tests passed!")

if __name__ == "__main__":
    try:
        test_dice_parsing()
        test_economy_volatility()
        test_consumable_resolution()
        print("\nAll unit tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        exit(1)
