from fastapi.testclient import TestClient
from event_gateway.main import app, init_db
from shared.schemas import EventPayload
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from event_gateway.service import AccountServiceUnavailable

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "up", "service": "event_gateway"}

@patch('event_gateway.service.EventGatewayService.call_account_service')
def test_submit_event_success(mock_call):
    mock_call.return_value = {"status": "success"}
    
    payload = {
        "eventId": "test-123",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 100.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/events", json=payload)
    assert response.status_code == 201
    assert response.json()["eventId"] == "test-123"
    
    # Test Idempotency
    response2 = client.post("/events", json=payload)
    assert response2.status_code == 201 # Idempotent request returns OK
    assert response2.json()["status"] == "duplicate"
    
@patch('event_gateway.service.EventGatewayService.call_account_service')
def test_submit_event_service_unavailable(mock_call):
    mock_call.side_effect = AccountServiceUnavailable("Down")
    
    payload = {
        "eventId": "test-fail",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 100.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/events", json=payload)
    assert response.status_code == 503
    assert response.json()["error"] == "Service Unavailable"
    assert response.json()["message"] == "Account Service is down"

def test_invalid_payload():
    payload = {
        "eventId": "test-invalid",
        "accountId": "acct-1",
        "type": "INVALID_TYPE",
        "amount": -50.0, # Negative amount
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/events", json=payload)
    assert response.status_code == 422 # FastAPI validation error
