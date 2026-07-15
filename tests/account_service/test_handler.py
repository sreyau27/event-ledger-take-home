from fastapi.testclient import TestClient
from account_service.main import app
import pytest
from unittest.mock import Mock

client = TestClient(app)

def test_apply_transaction_success():
    svc_mock = Mock()
    svc_mock.process_transaction.return_value = {"status": "success", "eventId": "evt-1"}
    
    from account_service.handler import get_account_service
    app.dependency_overrides[get_account_service] = lambda: svc_mock
    
    payload = {
        "eventId": "evt-1",
        "accountId": "acc-1",
        "type": "CREDIT",
        "amount": 100.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/accounts/acc-1/transactions", json=payload)
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["eventId"] == "evt-1"
    
    app.dependency_overrides.clear()

def test_apply_transaction_mismatch_account():
    payload = {
        "eventId": "evt-1",
        "accountId": "acc-different",
        "type": "CREDIT",
        "amount": 100.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z"
    }
    
    response = client.post("/accounts/acc-1/transactions", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Account ID in path must match payload"

def test_get_balance():
    svc_mock = Mock()
    svc_mock.calculate_balance.return_value = 250.0
    from account_service.handler import get_account_service
    app.dependency_overrides[get_account_service] = lambda: svc_mock
    
    response = client.get("/accounts/acc-1/balance")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["balance"] == 250.0
    
    app.dependency_overrides.clear()

def test_get_account_details():
    svc_mock = Mock()
    svc_mock.get_account_details.return_value = {"accountId": "acc-1", "balance": 250.0, "recentTransactions": []}
    from account_service.handler import get_account_service
    app.dependency_overrides[get_account_service] = lambda: svc_mock
    
    response = client.get("/accounts/acc-1")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["accountId"] == "acc-1"
    
    app.dependency_overrides.clear()
