from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import uuid
import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.schemas import EventPayload
from shared.logging import setup_logger, trace_id_ctx_var
from event_gateway.database import init_db, get_db
from event_gateway.models import EventRecord

logger = setup_logger("event_gateway")

app = FastAPI(title="Event Gateway API")

ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")

http_client = httpx.AsyncClient()

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Event Gateway started and DB initialized.")

@app.on_event("shutdown")
async def on_shutdown():
    await http_client.aclose()

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        trace_id = str(uuid.uuid4())
    trace_id_ctx_var.set(trace_id)
    
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response

@app.get("/health")
def health_check():
    return {"status": "up", "service": "event_gateway"}

class AccountServiceUnavailable(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, AccountServiceUnavailable)),
    reraise=True
)
async def call_account_service(payload: EventPayload, trace_id: str):
    logger.info(f"Calling Account Service for event {payload.eventId}")
    try:
        response = await http_client.post(
            f"{ACCOUNT_SERVICE_URL}/accounts/{payload.accountId}/transactions",
            json=payload.model_dump(),
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

@app.post("/events", status_code=201)
async def submit_event(payload: EventPayload, request: Request, db: Session = Depends(get_db)):
    trace_id = trace_id_ctx_var.get()
    
    existing_event = db.query(EventRecord).filter(EventRecord.event_id == payload.eventId).first()
    if existing_event:
        logger.info(f"Idempotency hit: Event {payload.eventId} already exists.")
        return {"status": "duplicate", "eventId": payload.eventId, "message": "Event already processed"}

    try:
        acct_response = await call_account_service(payload, trace_id)
    except AccountServiceUnavailable:
        logger.error("Account service is currently unavailable. Circuit breaker open / retries exhausted.")
        raise HTTPException(status_code=503, detail="Service Unavailable: Account Service is down")
    
    ts = payload.eventTimestamp.replace("Z", "+00:00")
    event_time = datetime.fromisoformat(ts)
    
    new_event = EventRecord(
        event_id=payload.eventId,
        account_id=payload.accountId,
        payload_json=payload.model_dump_json(),
        received_at=datetime.now(timezone.utc),
        event_timestamp=event_time
    )
    db.add(new_event)
    db.commit()
    logger.info(f"Event {payload.eventId} processed and saved.")
    
    return {"status": "success", "eventId": payload.eventId}

@app.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventRecord).filter(EventRecord.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return json.loads(event.payload_json)

@app.get("/events")
def list_events(account: str, db: Session = Depends(get_db)):
    events = db.query(EventRecord).filter(EventRecord.account_id == account).order_by(EventRecord.event_timestamp.asc()).all()
    return [json.loads(e.payload_json) for e in events]
