from unittest.mock import Mock
from datetime import datetime
from account_service.service import AccountServiceLogic

def test_process_transaction_new():
    repo_mock = Mock()
    repo_mock.get_by_event_id.return_value = None
    
    svc = AccountServiceLogic(repo_mock)
    dt = datetime.utcnow()
    result = svc.process_transaction("evt-1", "acc-1", "CREDIT", 100.0, "USD", dt)
    
    assert result == {"status": "success", "eventId": "evt-1"}
    repo_mock.create.assert_called_once_with(
        event_id="evt-1",
        account_id="acc-1",
        tx_type="CREDIT",
        amount=100.0,
        currency="USD",
        event_timestamp=dt
    )

def test_process_transaction_duplicate():
    repo_mock = Mock()
    repo_mock.get_by_event_id.return_value = Mock() # returning anything truthy
    
    svc = AccountServiceLogic(repo_mock)
    dt = datetime.utcnow()
    result = svc.process_transaction("evt-1", "acc-1", "CREDIT", 100.0, "USD", dt)
    
    assert result == {"status": "duplicate", "eventId": "evt-1"}
    repo_mock.create.assert_not_called()

def test_calculate_balance():
    repo_mock = Mock()
    mock_tx_1 = Mock(type="CREDIT", amount=150.0)
    mock_tx_2 = Mock(type="DEBIT", amount=50.0)
    mock_tx_3 = Mock(type="CREDIT", amount=10.0)
    repo_mock.get_by_account_id.return_value = [mock_tx_1, mock_tx_2, mock_tx_3]
    
    svc = AccountServiceLogic(repo_mock)
    balance = svc.calculate_balance("acc-1")
    
    # 150 - 50 + 10 = 110
    assert balance == 110.0
    repo_mock.get_by_account_id.assert_called_once_with("acc-1")

def test_get_account_details():
    repo_mock = Mock()
    mock_tx = Mock(event_id="evt-1", type="CREDIT", amount=150.0, currency="USD", event_timestamp=datetime(2026, 5, 15))
    repo_mock.get_by_account_id.return_value = [mock_tx]
    
    svc = AccountServiceLogic(repo_mock)
    details = svc.get_account_details("acc-1")
    
    assert details["accountId"] == "acc-1"
    assert details["balance"] == 150.0
    assert len(details["recentTransactions"]) == 1
    assert details["recentTransactions"][0]["eventId"] == "evt-1"
    assert details["recentTransactions"][0]["eventTimestamp"] == "2026-05-15T00:00:00"
    
    # Check that repo was called with limit and order_by_desc for the recent txs fetch
    repo_mock.get_by_account_id.assert_any_call("acc-1", limit=10, order_by_desc=True)
