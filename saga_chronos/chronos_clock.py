import math
import random

class ChronosClock:
    def __init__(self, calendar_config):
        self.months = calendar_config.get("months", [])
        self.seasons = calendar_config.get("seasons", {})
        self.days_of_week = calendar_config.get("days_of_week", ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"])
        self.moons = calendar_config.get("moons", [{"name": "Luna"}])
        
        # Calculate total days in one full custom year
        self.days_in_year = sum(m["days"] for m in self.months)

    def advance_time(self, current_tick, days_to_advance=1):
        """
        Advances the global clock by X days and determines what scope 
        of the simulation needs to run today.
        """
        new_tick = current_tick + days_to_advance
        
        # 3-Tiered Simulation Triggers
        run_local = True                    # Runs every single day
        run_regional = (new_tick % 7 == 0)  # Runs every 7 days
        run_global = (new_tick % 30 == 0)   # Runs every 30 days

        return {
            "new_tick": new_tick,
            "sim_triggers": {
                "local": run_local,
                "regional": run_regional,
                "global": run_global
            }
        }

    def get_current_date(self, current_tick):
        """
        Translates raw 'ticks' (total days since the dawn of time) 
        into your custom calendar date, season, and moon phase.
        """
        if self.days_in_year == 0:
            return None # Prevent division by zero if calendar is empty
            
        # 1. Calculate the Year
        year = (current_tick // self.days_in_year) + 1
        
        # 2. Calculate the Month and Day of the Month
        day_of_year = current_tick % self.days_in_year
        
        current_month = None
        day_of_month = day_of_year
        
        for month in self.months:
            if day_of_month < month["days"]:
                current_month = month
                break
            day_of_month -= month["days"]
            
        day_of_month += 1 # 1-indexed (e.g., The 1st of Sunfall)
        if current_month is None and len(self.months) > 0:
            current_month = self.months[-1] # Fallback
            
        # 3. Calculate Day of the Week
        weekday_name = self.days_of_week[current_tick % len(self.days_of_week)]

        # 4. Auto-Calculate Moon Phase (Syncs to the custom month length)
        # Calculates where we are in the month as a percentage (0.0 to 1.0)
        month_progress = day_of_month / current_month["days"] if current_month and current_month["days"] > 0 else 0
        moon_phase = self._calculate_moon_phase(month_progress)

        return {
            "year": year,
            "month": current_month["name"] if current_month else "Unknown",
            "day": day_of_month,
            "weekday": weekday_name,
            "season": current_month["season"] if current_month else "Unknown",
            "moon": {
                "name": self.moons[0]["name"] if self.moons else "Moon",
                "phase": moon_phase
            }
        }

    def _calculate_moon_phase(self, progress):
        """ Translates mathematical progress into visual moon phases. """
        if progress < 0.05: return "New Moon"
        elif progress < 0.25: return "Waxing Crescent"
        elif progress < 0.45: return "First Quarter"
        elif progress < 0.55: return "Full Moon"
        elif progress < 0.75: return "Waning Gibbous"
        elif progress < 0.95: return "Last Quarter"
        else: return "Waning Crescent"

    def calculate_hex_weather(self, hex_base_temp, current_season):
        """
        Takes the C++ base temperature for a specific hex and calculates today's 
        actual temperature by cutting the area's total variance range into thirds.
        """
        season_rules = self.seasons.get(current_season, {"temp_band": "MID", "precipitation_chance": 0})
        
        # 1. Define the area's total temperature swing (e.g., +/- 24 degrees from average)
        # (In the future, we can make variance larger for poles, smaller for equator)
        variance = 24  
        min_temp = hex_base_temp - variance
        max_temp = hex_base_temp + variance
        
        # 2. Cut the range into 3 equal parts
        range_size = (max_temp - min_temp) / 3
        
        low_cutoff = min_temp + range_size
        high_cutoff = max_temp - range_size

        # 3. Roll today's temperature based on the Season's designated band
        band = season_rules.get("temp_band", "MID")
        
        if band == "LOW":
            # Winter range
            daily_temp = random.uniform(min_temp, low_cutoff)
        elif band == "MID":
            # Spring / Fall range
            daily_temp = random.uniform(low_cutoff, high_cutoff)
        elif band == "HIGH":
            # Summer range
            daily_temp = random.uniform(high_cutoff, max_temp)
        else:
             daily_temp = hex_base_temp # Fallback
            
        # 4. Roll for precipitation
        is_precipitating = random.random() < season_rules.get("precipitation_chance", 0)
        active_weather = season_rules.get("weather_type", "Clear") if is_precipitating else "Clear"
        
        # Special physics logic: If it's raining but the temp is below freezing, it becomes snow
        if active_weather == "Rain" and daily_temp < 0: # Using 0C for freezing, assuming C++ outputs Celsius
            active_weather = "Snow"

        return {
            "temperature": round(daily_temp, 1),
            "weather": active_weather
        }
