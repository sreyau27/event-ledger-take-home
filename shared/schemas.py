from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any

class EventPayload(BaseModel):
    eventId: str
    accountId: str
    type: str
    amount: float
    currency: str
    eventTimestamp: str  # ISO 8601 string
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('type')
    def validate_type(cls, v):
        if v not in ('CREDIT', 'DEBIT'):
            raise ValueError('Type must be CREDIT or DEBIT')
        return v
        
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v
