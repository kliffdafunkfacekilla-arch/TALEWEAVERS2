import math
import random

class ChronosClock:
    def __init__(self, calendar_config):
        self.months = calendar_config.get("months", [])
        self.seasons = calendar_config.get("seasons", {})
        self.days_of_week = calendar_config.get("days_of_week", ["Firstday", "Midday", "Thirdday", "Moonday", "Titansday", "Starday", "Restday"])
        self.moons = calendar_config.get("moons", [{"name": "Cruorbus", "color_resting": "Purple"}])
        self.intercalary = calendar_config.get("intercalary_periods", [])
        self.special_alignments = calendar_config.get("special_alignments", [])

        # Total days in one full named-month year (before intercalary)
        self.days_in_year = sum(m["days"] for m in self.months)

        # Duration of the intercalary period (Shadow Week = 7 days)
        self.shadow_week_days = sum(p["days"] for p in self.intercalary) if self.intercalary else 0

        # Full calendar year including Shadow Week
        self.full_year_days = self.days_in_year + self.shadow_week_days

        # Build the primary moon reference (Cruorbus)
        self.cruorbus = next((m for m in self.moons if m["name"] == "Cruorbus"), self.moons[0] if self.moons else {})
        self.erranith  = next((m for m in self.moons if m["name"] == "Erranith"),  None)

    def advance_time(self, current_tick, days_to_advance=1):
        """
        Advances the global clock by X days and determines what scope
        of the simulation needs to run.
        """
        new_tick = current_tick + days_to_advance

        run_local    = True                    # Every day
        run_regional = (new_tick % 7 == 0)     # Every 7 days (one week)
        run_global   = (new_tick % 30 == 0)    # Every 30 days (one month)

        return {
            "new_tick": new_tick,
            "sim_triggers": {
                "local":    run_local,
                "regional": run_regional,
                "global":   run_global
            }
        }

    def get_current_date(self, current_tick):
        """
        Translates raw ticks (total days since the world began) into
        a fully detailed Ostraka calendar date, including:
        - Named month, day, year
        - Season with chaos modifier
        - Cruorbus moon phase and chromatic state
        - Erranith proximity flag
        - Shadow Week detection
        - Special alignment detection
        """
        if self.full_year_days == 0:
            return None

        # Which year and which day within that year?
        year          = (current_tick // self.full_year_days) + 1
        day_of_year   = current_tick % self.full_year_days

        # --- Shadow Week detection ---
        is_shadow_week = day_of_year >= self.days_in_year
        shadow_week_day = (day_of_year - self.days_in_year + 1) if is_shadow_week else None

        if is_shadow_week:
            return {
                "year":         year,
                "month":        "Shadow Week",
                "day":          shadow_week_day,
                "weekday":      self.days_of_week[current_tick % len(self.days_of_week)],
                "season":       "Shadow Week",
                "is_shadow_week": True,
                "shadow_week_events": self.intercalary[0].get("special_events", []) if self.intercalary else [],
                "chaos_modifier": 5.0,
                "moon": {
                    "primary":  {"name": "Cruorbus", "phase": "Total Eclipse", "color": "Black — wound hidden in darkness"},
                    "secondary": {"name": "Erranith", "phase": "Alignment", "note": "Ghost Moon causes the eclipse"}
                }
            }

        # --- Normal month/day resolution ---
        current_month  = None
        day_of_month   = day_of_year

        for month in self.months:
            if day_of_month < month["days"]:
                current_month = month
                break
            day_of_month -= month["days"]

        day_of_month += 1  # 1-indexed
        if current_month is None and self.months:
            current_month = self.months[-1]

        # --- Weekday ---
        weekday_name = self.days_of_week[current_tick % len(self.days_of_week)]

        # --- Season data ---
        season_name  = current_month.get("season", "Unknown") if current_month else "Unknown"
        season_rules = self.seasons.get(season_name, {})
        chaos_mod    = season_rules.get("chaos_modifier", 1.0)

        # --- Cruorbus moon phase (from month lore data) ---
        moon_phase_name = current_month.get("moon_phase", "Unknown") if current_month else "Unknown"
        moon_color      = current_month.get("moon_color",  "Purple")  if current_month else "Purple"

        # Day-level light phase: standard New/Waxing/Full/Waning driven by day_of_month
        month_progress = (day_of_month / current_month["days"]) if current_month and current_month["days"] > 0 else 0
        light_phase    = self._calculate_light_phase(month_progress)

        # --- Check special alignments ---
        active_alignment = None
        if moon_phase_name == "The Open Eye":
            if light_phase == "Full Moon":              # Nightmare Alignment
                active_alignment = self.special_alignments[0] if len(self.special_alignments) > 0 else None
                chaos_mod = (active_alignment or {}).get("chaos_modifier", chaos_mod)
            elif light_phase == "New Moon":             # Mercy Alignment
                active_alignment = self.special_alignments[1] if len(self.special_alignments) > 1 else None
                chaos_mod = (active_alignment or {}).get("chaos_modifier", chaos_mod)

        # --- Erranith (Ghost Moon) proximity ---
        erranith_nearby = False
        if self.erranith:
            erranith_cycle = self.erranith.get("orbital_cycle_days", self.full_year_days)
            erranith_position = current_tick % erranith_cycle
            # Ghost moon is "close" in the final 15% of its orbit
            erranith_nearby = erranith_position > (erranith_cycle * 0.85)
            if erranith_nearby and moon_phase_name == "The Open Eye":
                active_alignment = self.special_alignments[2] if len(self.special_alignments) > 2 else None
                chaos_mod = (active_alignment or {}).get("chaos_modifier", chaos_mod)

        # --- Weather ---
        weather = self.calculate_hex_weather(20, season_name)

        return {
            "year":          year,
            "month":         current_month["name"] if current_month else "Unknown",
            "day":           day_of_month,
            "weekday":       weekday_name,
            "season":        season_name,
            "is_shadow_week": False,
            "chaos_modifier": round(chaos_mod, 2),
            "moon": {
                "primary": {
                    "name":        "Cruorbus",
                    "orbital_phase": moon_phase_name,
                    "light_phase": light_phase,
                    "color":       moon_color,
                    "is_surging":  moon_color == "Red"
                },
                "secondary": {
                    "name":    "Erranith",
                    "nearby":  erranith_nearby,
                    "note":    "Ghost Moon approaching — chaos surge imminent!" if erranith_nearby else "Ghost Moon distant"
                }
            },
            "active_alignment": active_alignment["name"] if active_alignment else None,
            "weather":       weather
        }

    def _calculate_light_phase(self, progress):
        """Translates the day-within-month progress to a standard light phase name for Cruorbus."""
        if progress < 0.05:   return "New Moon"
        elif progress < 0.25: return "Waxing Crescent"
        elif progress < 0.45: return "First Quarter"
        elif progress < 0.55: return "Full Moon"
        elif progress < 0.75: return "Waning Gibbous"
        elif progress < 0.95: return "Last Quarter"
        else:                 return "Waning Crescent"

    def calculate_hex_weather(self, hex_base_temp, current_season):
        """
        Takes the hex base temperature and calculates today's weather
        using the season rules and chaos modifier for Ostraka.
        """
        season_rules = self.seasons.get(current_season, {"temp_band": "MID", "precipitation_chance": 0})
        if current_season == "Shadow Week":
            return {"temperature": hex_base_temp - 10, "weather": "Eclipse Darkness"}

        variance = 24
        min_temp  = hex_base_temp - variance
        max_temp  = hex_base_temp + variance
        range_sz  = (max_temp - min_temp) / 3
        low_cut   = min_temp + range_sz
        high_cut  = max_temp - range_sz

        band = season_rules.get("temp_band", "MID")
        if band == "LOW":
            daily_temp = random.uniform(min_temp, low_cut)
        elif band == "HIGH":
            daily_temp = random.uniform(high_cut, max_temp)
        else:
            daily_temp = random.uniform(low_cut, high_cut)

        is_precipitating = random.random() < season_rules.get("precipitation_chance", 0)
        active_weather   = season_rules.get("weather_type", "Clear") if is_precipitating else "Clear"

        if active_weather == "Rain" and daily_temp < 0:
            active_weather = "Snow"

        return {
            "temperature": round(daily_temp, 1),
            "weather":     active_weather
        }

    def get_chaos_modifier(self, current_tick):
        """Convenience method — returns just the numerical chaos modifier for the current tick."""
        date = self.get_current_date(current_tick)
        return date.get("chaos_modifier", 1.0) if date else 1.0

    def is_shadow_week(self, current_tick):
        """Returns True if the current tick falls within the Shadow Week intercalary period."""
        if self.full_year_days == 0:
            return False
        day_of_year = current_tick % self.full_year_days
        return day_of_year >= self.days_in_year
