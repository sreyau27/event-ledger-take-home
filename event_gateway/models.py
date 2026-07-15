from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class EventRecord(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, index=True, nullable=False)
    payload_json = Column(Text, nullable=False)
    received_at = Column(DateTime, nullable=False)
    event_timestamp = Column(DateTime, nullable=False)
