from sqlalchemy.orm import Session
from datetime import datetime
from event_gateway.models import EventRecord

class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_event_id(self, event_id: str):
        return self.db.query(EventRecord).filter(EventRecord.event_id == event_id).first()

    def get_by_account_id(self, account_id: str):
        return self.db.query(EventRecord).filter(EventRecord.account_id == account_id).order_by(EventRecord.event_timestamp.asc()).all()

    def create(self, event_id: str, account_id: str, payload_json: str, received_at: datetime, event_timestamp: datetime):
        new_event = EventRecord(
            event_id=event_id,
            account_id=account_id,
            payload_json=payload_json,
            received_at=received_at,
            event_timestamp=event_timestamp
        )
        self.db.add(new_event)
        self.db.commit()
        return new_event
