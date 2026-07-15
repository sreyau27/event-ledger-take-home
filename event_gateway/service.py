import httpx
import os
import json
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.schemas import EventPayload
from shared.logging import setup_logger
from shared.exceptions import AccountServiceUnavailable
from event_gateway.repository import EventRepository

logger = setup_logger("event_gateway")
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")

class EventGatewayService:
    def __init__(self, repo: EventRepository, http_client: httpx.AsyncClient):
        self.repo = repo
        self.http_client = http_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, AccountServiceUnavailable)),
        reraise=True
    )
    async def call_account_service(self, payload: EventPayload, trace_id: str):
        logger.info(f"Calling Account Service for event {payload.eventId}")
        try:
            response = await self.http_client.post(
                f"{ACCOUNT_SERVICE_URL}/accounts/{payload.accountId}/transactions",
                json=payload.model_dump(mode='json'),
                headers={"X-Trace-Id": trace_id}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error calling Account Service: {e}")
            raise AccountServiceUnavailable(f"Account Service Unreachable: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Account Service: {e.response.status_code}")
            if e.response.status_code >= 500:
                raise AccountServiceUnavailable(f"Account Service Error: {e.response.status_code}")
            return e.response.json()

    async def process_event(self, payload: EventPayload, trace_id: str):
        account_response = await self.call_account_service(payload, trace_id)
        
        if isinstance(account_response, dict) and not account_response.get("success", True):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=account_response.get("message", "Account Service rejected the event"))
            
        event, created = self.repo.create(
            event_id=payload.eventId,
            account_id=payload.accountId,
            payload_json=payload.model_dump_json(),
            received_at=datetime.now(timezone.utc),
            event_timestamp=payload.eventTimestamp
        )
        
        if not created:
            logger.info(f"Idempotency hit: Event {payload.eventId} already exists.")
            return {"status": "duplicate", "eventId": payload.eventId, "message": "Event already processed"}

        logger.info(f"Event {payload.eventId} processed and saved.")
        return {"status": "success", "eventId": payload.eventId}

    def get_event(self, event_id: str):
        event = self.repo.get_by_event_id(event_id)
        if not event:
            return None
        return json.loads(event.payload_json)

    def list_events(self, account_id: str):
        events = self.repo.get_by_account_id(account_id)
        return [json.loads(e.payload_json) for e in events]
