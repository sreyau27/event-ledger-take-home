from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None
    trace_id: Optional[str] = None
class EventPayload(BaseModel):
    eventId: str
    accountId: str
    type: str
    amount: float
    currency: str
    eventTimestamp: datetime
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
