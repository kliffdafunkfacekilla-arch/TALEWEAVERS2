import logging
from .models import CampaignState, WorldEventsLog
from .database import SessionLocal

logger = logging.getLogger("saga_director.day_clock")

PHASES = ["DAWN", "MORNING", "AFTERNOON", "EVENING", "NIGHT"]

class DayClock:
    def __init__(self, campaign_id: str):
        self.campaign_id = campaign_id

    def get_current_phase(self) -> str:
        """Retrieves the current day phase from the database."""
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if not state:
                return "MORNING"
            return state.day_phase or "MORNING"
        finally:
            db.close()

    def get_current_day(self) -> int:
        """Retrieves the current day from the database."""
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if not state:
                return 1
            return state.day or 1
        finally:
            db.close()

    def advance_phase(self) -> str:
        """Advances to the next phase. If NIGHT is finished, advances to next day."""
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if not state:
                return "MORNING"

            current = state.day_phase or "MORNING"
            current_idx = PHASES.index(current)
            
            if current == "NIGHT":
                state.day_phase = "DAWN"
                state.day += 1
                new_phase = "DAWN"
                self._emit_day_advanced(db, state.day)
            else:
                new_phase = PHASES[current_idx + 1]
                state.day_phase = new_phase

            db.commit()
            logger.info(f"[CLOCK] Campaign {self.campaign_id} advanced to {new_phase}, Day {state.day}")
            return new_phase
        finally:
            db.close()

    def set_phase(self, phase: str):
        """Manually sets the phase (e.g., from DM command)."""
        if phase not in PHASES:
            raise ValueError(f"Invalid phase: {phase}")
        
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if state:
                state.day_phase = phase
                db.commit()
        finally:
            db.close()

    def long_rest(self):
        """Resets clock to DAWN and advances day."""
        db = SessionLocal()
        try:
            state = db.query(CampaignState).filter(CampaignState.id == self.campaign_id).first()
            if state:
                state.day += 1
                state.day_phase = "DAWN"
                db.commit()
                self._emit_day_advanced(db, state.day)
        finally:
            db.close()

    def _emit_day_advanced(self, db, new_day: int):
        """Emits a DAY_ADVANCED event to the Chronicle Ledger."""
        # Note: Chronicle Ledger in this architecture is the WorldEventsLog table
        event = WorldEventsLog(
            campaign_id=self.campaign_id,
            event_description=f"Day {new_day} has dawned.",
            turn_number=new_day
        )
        db.add(event)
        # We don't commit here because this is called inside another transaction
