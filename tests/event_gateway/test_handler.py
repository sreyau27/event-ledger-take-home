import pytest
from http import HTTPStatus
from fastapi.testclient import TestClient
from event_gateway.main import app
from unittest.mock import AsyncMock, Mock
from shared.exceptions import AccountServiceUnavailable

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["success"] is True
    assert response.json()["data"] == {"status": "up", "service": "event_gateway"}

def test_submit_event_success():
    svc_mock = Mock()
    svc_mock.process_event = AsyncMock(return_value={"status": "success", "eventId": "evt-1"})
    
    from event_gateway.handler import get_gateway_service
    app.dependency_overrides[get_gateway_service] = lambda: svc_mock
    
    payload = {
        "eventId": "test-123",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 100.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/events", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()["success"] is True
    assert response.json()["data"]["eventId"] == "evt-1"
    app.dependency_overrides.clear()

def test_submit_event_service_unavailable():
    svc_mock = Mock()
    svc_mock.process_event = AsyncMock(side_effect=AccountServiceUnavailable("Down"))
    
    from event_gateway.handler import get_gateway_service
    app.dependency_overrides[get_gateway_service] = lambda: svc_mock
    
    payload = {
        "eventId": "test-fail",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 100.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/events", json=payload)
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json()["success"] is False
    assert response.json()["error"] == "Service Unavailable"
    app.dependency_overrides.clear()

def test_invalid_payload():
    payload = {
        "eventId": "test-invalid",
        "accountId": "acct-1",
        "type": "INVALID_TYPE",
        "amount": -50.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/events", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["success"] is False
    assert response.json()["error"] == "Validation Error"

def test_get_event():
    svc_mock = Mock()
    svc_mock.get_event.return_value = {"eventId": "evt-1", "type": "CREDIT"}
    
    from event_gateway.handler import get_gateway_service
    app.dependency_overrides[get_gateway_service] = lambda: svc_mock
    
    response = client.get("/events/evt-1")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["success"] is True
    assert response.json()["data"]["eventId"] == "evt-1"
    
    # Not found
    svc_mock.get_event.return_value = None
    response_not_found = client.get("/events/evt-2")
    assert response_not_found.status_code == HTTPStatus.NOT_FOUND
    
    app.dependency_overrides.clear()

def test_list_events():
    svc_mock = Mock()
    svc_mock.list_events.return_value = [{"eventId": "evt-1"}, {"eventId": "evt-2"}]
    
    from event_gateway.handler import get_gateway_service
    app.dependency_overrides[get_gateway_service] = lambda: svc_mock
    
    response = client.get("/events?account=acc-1")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 2
    app.dependency_overrides.clear()
