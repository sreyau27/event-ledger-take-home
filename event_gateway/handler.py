from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from shared.schemas import EventPayload
from shared.logging import setup_logger, trace_id_ctx_var
from event_gateway.database import get_db
from event_gateway.repository import EventRepository
from event_gateway.service import EventGatewayService, AccountServiceUnavailable

logger = setup_logger("event_gateway")
router = APIRouter()

http_client = httpx.AsyncClient()

def get_gateway_service(db: Session = Depends(get_db)):
    repo = EventRepository(db)
    return EventGatewayService(repo, http_client)

@router.post("/events", status_code=201)
async def submit_event(payload: EventPayload, svc: EventGatewayService = Depends(get_gateway_service)):
    trace_id = trace_id_ctx_var.get()
    
    try:
        result = await svc.process_event(payload, trace_id)
        return result
    except AccountServiceUnavailable:
        logger.error("Account service is currently unavailable. Circuit breaker open / retries exhausted.")
        raise HTTPException(status_code=503, detail="Service Unavailable: Account Service is down")

@router.get("/events/{event_id}")
def get_event(event_id: str, svc: EventGatewayService = Depends(get_gateway_service)):
    event = svc.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events")
def list_events(account: str, svc: EventGatewayService = Depends(get_gateway_service)):
    return svc.list_events(account)
