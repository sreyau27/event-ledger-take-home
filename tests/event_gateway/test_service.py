import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
import httpx
from shared.schemas import EventPayload
from shared.exceptions import AccountServiceUnavailable
from event_gateway.service import EventGatewayService

@pytest.fixture
def payload():
    return EventPayload(
        eventId="evt-1",
        accountId="acc-1",
        type="CREDIT",
        amount=100.0,
        currency="USD",
        eventTimestamp=datetime(2026, 5, 15, tzinfo=timezone.utc)
    )

@pytest.mark.anyio
async def test_process_event_duplicate(payload):
    repo_mock = Mock()
    repo_mock.get_by_event_id.return_value = Mock()
    
    http_mock = AsyncMock()
    svc = EventGatewayService(repo_mock, http_mock)
    
    result = await svc.process_event(payload, "trace-123")
    assert result == {"status": "duplicate", "eventId": "evt-1", "message": "Event already processed"}
    http_mock.post.assert_not_called()
    repo_mock.create.assert_not_called()

@pytest.mark.anyio
async def test_process_event_success(payload):
    repo_mock = Mock()
    repo_mock.get_by_event_id.return_value = None
    
    http_mock = AsyncMock()
    response_mock = Mock()
    response_mock.json.return_value = {"status": "success", "eventId": "evt-1"}
    response_mock.raise_for_status = Mock()
    http_mock.post.return_value = response_mock
    
    svc = EventGatewayService(repo_mock, http_mock)
    result = await svc.process_event(payload, "trace-123")
    
    assert result == {"status": "success", "eventId": "evt-1"}
    http_mock.post.assert_called_once()
    repo_mock.create.assert_called_once()

@pytest.mark.anyio
async def test_process_event_account_service_500(payload):
    repo_mock = Mock()
    repo_mock.get_by_event_id.return_value = None
    
    http_mock = AsyncMock()
    response_mock = Mock()
    response_mock.status_code = 500
    
    def raise_http_error():
        raise httpx.HTTPStatusError("500 Error", request=Mock(), response=response_mock)
        
    response_mock.raise_for_status.side_effect = raise_http_error
    http_mock.post.return_value = response_mock
    
    svc = EventGatewayService(repo_mock, http_mock)
    
    # It should retry 3 times according to tenacity setup, then raise AccountServiceUnavailable
    with pytest.raises(AccountServiceUnavailable) as exc:
        await svc.process_event(payload, "trace-123")
        
    assert "Account Service Error: 500" in str(exc.value)
    # 3 attempts
    assert http_mock.post.call_count == 3
    repo_mock.create.assert_not_called()

@pytest.mark.anyio
async def test_process_event_account_service_unreachable(payload):
    repo_mock = Mock()
    repo_mock.get_by_event_id.return_value = None
    
    http_mock = AsyncMock()
    http_mock.post.side_effect = httpx.RequestError("Connection Refused")
    
    svc = EventGatewayService(repo_mock, http_mock)
    
    with pytest.raises(AccountServiceUnavailable) as exc:
        await svc.process_event(payload, "trace-123")
        
    assert "Account Service Unreachable" in str(exc.value)
    # 3 attempts
    assert http_mock.post.call_count == 3
    repo_mock.create.assert_not_called()
