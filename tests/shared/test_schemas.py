import pytest
from pydantic import ValidationError
from datetime import datetime
from shared.schemas import EventPayload, APIResponse

def test_event_payload_valid():
    payload = EventPayload(
        eventId="evt-1",
        accountId="acc-1",
        type="CREDIT",
        amount=100.0,
        currency="USD",
        eventTimestamp="2026-05-15T14:02:11Z",
        metadata={"source": "test"}
    )
    assert payload.type == "CREDIT"
    assert payload.amount == 100.0
    assert isinstance(payload.eventTimestamp, datetime)
    assert payload.metadata == {"source": "test"}

def test_event_payload_invalid_type():
    with pytest.raises(ValidationError) as exc_info:
        EventPayload(
            eventId="evt-1",
            accountId="acc-1",
            type="INVALID_TYPE",
            amount=100.0,
            currency="USD",
            eventTimestamp="2026-05-15T14:02:11Z"
        )
    assert "Type must be CREDIT or DEBIT" in str(exc_info.value)

def test_event_payload_invalid_amount():
    with pytest.raises(ValidationError) as exc_info:
        EventPayload(
            eventId="evt-1",
            accountId="acc-1",
            type="DEBIT",
            amount=-50.0,
            currency="USD",
            eventTimestamp="2026-05-15T14:02:11Z"
        )
    assert "Amount must be greater than 0" in str(exc_info.value)

def test_event_payload_invalid_timestamp():
    with pytest.raises(ValidationError):
        EventPayload(
            eventId="evt-1",
            accountId="acc-1",
            type="CREDIT",
            amount=100.0,
            currency="USD",
            eventTimestamp="not-a-timestamp"
        )

def test_api_response_schema():
    resp = APIResponse(success=True, data={"foo": "bar"}, trace_id="123")
    assert resp.success is True
    assert resp.data == {"foo": "bar"}
    assert resp.error is None
