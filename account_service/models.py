from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    account_id = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    event_timestamp = Column(DateTime, nullable=False)
