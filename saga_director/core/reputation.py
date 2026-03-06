import logging
from .models import CampaignState, WorldEventsLog
from .database import SessionLocal

logger = logging.getLogger("saga_director.reputation")

ATTITUDE_THRESHOLDS = {
    "FRIENDLY": 50,
    "NEUTRAL": 0,
    "HOSTILE": -1,
    "WANTED": -50
}

EVENT_SCORES = {
    "aided": 20,
    "quest_complete": 30,
    "traded": 10,
    "raided": -40,
    "killed_member": -25,
    "killed_leader": -100
}

class FactionReputation:
    def __init__(self, campaign_id: str):
        self.campaign_id = campaign_id

    def get_all_attitudes(self) -> dict:
        """Returns the calculated attitude for all factions for this campaign."""
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if not state:
                return {}
            
            reputation_data = state.reputation or {}
            attitudes = {}
            for faction, score in reputation_data.items():
                attitudes[faction] = self._score_to_tier(score)
            return attitudes
        finally:
            db.close()

    def get_attitude(self, faction_name: str) -> str:
        """Returns the attitude tier for a specific faction."""
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if not state:
                return "NEUTRAL"
            
            score = (state.reputation or {}).get(faction_name, 0)
            return self._score_to_tier(score)
        finally:
            db.close()

    def apply_event(self, faction_name: str, event_type: str):
        """Updates the reputation score based on an action type."""
        score_change = EVENT_SCORES.get(event_type, 0)
        if score_change == 0:
            return

        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if state:
                rep = dict(state.reputation or {})
                current_score = rep.get(faction_name, 0)
                rep[faction_name] = current_score + score_change
                state.reputation = rep
                db.commit()
                logger.info(f"[REP] Faction {faction_name} reputation shift: {score_change} (New score: {rep[faction_name]})")
        finally:
            db.close()

    def _score_to_tier(self, score: int) -> str:
        """Maps a raw score to an attitude tier."""
        if score <= ATTITUDE_THRESHOLDS["WANTED"]:
            return "WANTED"
        if score <= ATTITUDE_THRESHOLDS["HOSTILE"]:
            return "HOSTILE"
        if score >= ATTITUDE_THRESHOLDS["FRIENDLY"]:
            return "FRIENDLY"
        return "NEUTRAL"

    def sync_from_ledger(self):
        """
        Scan WorldEventsLog for existing faction-related events 
        and rebuild the reputation scores (idempotent).
        """
        db = SessionLocal()
        try:
            events = db.query(WorldEventsLog).filter(
                WorldEventsLog.campaign_id == self.campaign_id,
                WorldEventsLog.associated_faction.isnot(None)
            ).all()

            new_rep = {}
            for ev in events:
                faction = ev.associated_faction
                desc = (ev.event_description or "").lower()
                
                # Heuristic mapping for ledger descriptions
                score_delta = 0
                if "aided" in desc or "helped" in desc:
                    score_delta = EVENT_SCORES["aided"]
                elif "completed" in desc and "quest" in desc:
                    score_delta = EVENT_SCORES["quest_complete"]
                elif "traded" in desc:
                    score_delta = EVENT_SCORES["traded"]
                elif "raided" in desc or "attacked" in desc:
                    score_delta = EVENT_SCORES["raided"]
                elif "slew" in desc or "killed" in desc:
                    score_delta = EVENT_SCORES["killed_member"]
                elif "slew" in desc and "leader" in desc:
                    score_delta = EVENT_SCORES["killed_leader"]

                new_rep[faction] = new_rep.get(faction, 0) + score_delta

            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if state:
                state.reputation = new_rep
                db.commit()
                logger.info(f"[REP] Rebuilt reputation from ledger for {self.campaign_id}")
        finally:
            db.close()
