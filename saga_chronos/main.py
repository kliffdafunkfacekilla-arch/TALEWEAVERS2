from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from chronos_clock import ChronosClock
import json
import os
from pydantic import BaseModel

app = FastAPI(title="S.A.G.A. Chronos Engine", description="Module 4: Time & Weather")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a path for the config file
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
CALENDAR_FILE = os.path.join(DATA_DIR, "calendar_rules.json")

# Default template if the file doesn't exist yet
DEFAULT_CALENDAR = {
  "months": [
    {"name": "Dawnspire", "days": 30, "season": "Spring"},
    {"name": "Floralis", "days": 30, "season": "Spring"},
    {"name": "Greenbloom", "days": 30, "season": "Spring"},
    {"name": "Goldensun", "days": 30, "season": "Summer"},
    {"name": "Highfever", "days": 30, "season": "Summer"},
    {"name": "Sunsear", "days": 30, "season": "Summer"},
    {"name": "Harvestride", "days": 30, "season": "Autumn"},
    {"name": "Embershake", "days": 30, "season": "Autumn"},
    {"name": "Leafsfall", "days": 30, "season": "Autumn"},
    {"name": "Frostveil", "days": 30, "season": "Winter"},
    {"name": "Deepbite", "days": 30, "season": "Winter"},
    {"name": "Ironwind", "days": 30, "season": "Winter"}
  ],
  "seasons": {
    "Spring": { "temp_band": "MID", "precipitation_chance": 0.4, "weather_type": "Rain" },
    "Summer": { "temp_band": "HIGH", "precipitation_chance": 0.2, "weather_type": "Rain" },
    "Autumn": { "temp_band": "MID", "precipitation_chance": 0.6, "weather_type": "Rain" },
    "Winter": { "temp_band": "LOW", "precipitation_chance": 0.3, "weather_type": "Snow" }
  },
  "moons": [{"name": "Aetheris", "color": "Pale Blue"}],
  "days_of_week": ["Firstday", "Midday", "Thirdday", "Moonday", "Titansday", "Starday", "Restday"]
}

def load_calendar():
    if not os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "w") as f:
            json.dump(DEFAULT_CALENDAR, f, indent=2)
        return DEFAULT_CALENDAR
    try:
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading calendar config: {e}. Reverting to default.")
        return DEFAULT_CALENDAR

# Initialize the clock
current_config = load_calendar()
clock = ChronosClock(current_config)

class TickRequest(BaseModel):
    current_tick: int
    days_to_advance: int = 1

@app.get("/api/config/calendar")
async def get_calendar():
    return load_calendar()

@app.post("/api/config/calendar")
async def save_calendar(request: dict):
    global clock, current_config
    try:
        with open(CALENDAR_FILE, "w") as f:
            json.dump(request, f, indent=2)
        
        # Hot-reload the clock engine with the new rules
        current_config = request
        clock = ChronosClock(current_config)
        
        return {"status": "success", "message": "Calendar rules updated and Chronos restarted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save calendar: {e}")

@app.post("/api/chronos/tick")
async def advance_clock(req: TickRequest):
    """
    Advances the clock and returns the new date and the LOD simulation triggers.
    """
    try:
        time_data = clock.advance_time(req.current_tick, req.days_to_advance)
        date_data = clock.get_current_date(time_data["new_tick"])
        
        return {
            "status": "success",
            "time_data": time_data,
            "date": date_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "Chronos Engine", "port": 9000}

if __name__ == "__main__":
    import uvicorn
    # Module 4 runs on Port 9000
    uvicorn.run(app, host="0.0.0.0", port=9000)
