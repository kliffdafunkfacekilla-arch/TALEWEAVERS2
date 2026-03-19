from core.resonance_logic import calculate_resonance

def test_resonance():
    # Test favored biome
    bonus, flavor = calculate_resonance("VITA", "Jungle", "Clear Skies")
    assert bonus == 1
    assert "resonates with your VITA essence" in flavor

    # Test hindered biome
    bonus, flavor = calculate_resonance("LUX", "Cave", "Clear Skies")
    assert bonus == 0 # -1 (biome) + 1 (weather) = 0
    assert "dampens your magical focus" not in flavor # Weather is favored, but bonus sums to 0

    # Test favored weather
    bonus, flavor = calculate_resonance("ANUMIS", "Tundra", "Toxic Fog")
    assert bonus == 1
    assert "acts as a conduit for your power" in flavor

    # Test neutral
    bonus, flavor = calculate_resonance("NEXUS", "Plains", "Overcast")
    assert bonus == 0
    assert flavor == "The weave is stable in this environment."

    print("Targeted resonance logic tests passed!")

if __name__ == "__main__":
    test_resonance()
