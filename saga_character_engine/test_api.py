from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_character_calculation():
    payload = {
        "name": "Thorn",
        "base_attributes": {
            "might": 10, "endurance": 10, "vitality": 10,
            "fortitude": 10, "reflexes": 10, "finesse": 10,
            "knowledge": 10, "logic": 10, "charm": 10,
            "willpower": 10, "awareness": 10, "intuition": 10
        },
        "evolutions": {
            "species_base": "PLANT",
            "skin_slot": "Cactus Spines",
            "body_slot": "IronBark"
        },
        "background_training": "Soldier",
        "selected_powers": ["Vine Lash"],
        "equipped_loadout": {
            "armor": "Scale Mail",
            "weapon": "Greatsword"
        }
    }
    
    response = client.post("/api/rules/character/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # 1. Check Attribute Bonuses from Evolutions
    # Cactus Spines: +1 reflexes, +1 awareness
    # IronBark: +2 fortitude
    # Base was 10.
    assert data["attributes"]["reflexes"] == 11
    assert data["attributes"]["awareness"] == 11
    assert data["attributes"]["fortitude"] == 12
    
    # 2. Check Survival Pools (Math)
    # max_hp = might(10) + reflexes(11) + vitality(10) = 31
    # max_stamina = endurance(10) + fortitude(12) + finesse(10) = 32
    # max_composure = willpower(10) + logic(10) + awareness(11) = 31
    # max_focus = knowledge(10) + charm(10) + intuition(10) = 30
    assert data["vitals"]["max_hp"] == 31
    assert data["vitals"]["max_stamina"] == 32
    assert data["vitals"]["max_composure"] == 31
    assert data["vitals"]["max_focus"] == 30
    
    # 3. Check Passives
    passives = [p["name"] for p in data["passives"]]
    assert "Needle Burst" in passives
    assert "Hardened Shell" in passives
    
    # 4. Check Holding Fees
    # Scale Mail: 2 stamina
    # Greatsword: 1 stamina
    assert data["holding_fees"]["stamina"] == 3
    assert data["holding_fees"]["focus"] == 0

    print("Verification Successful: All TALEWEAVERS rules applied correctly.")

if __name__ == "__main__":
    test_health()
    test_character_calculation()
