from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus
from sqlalchemy.orm import Session
from shared.schemas import EventPayload, APIResponse
from shared.logging import setup_logger, trace_id_ctx_var
from account_service.database import get_db
from account_service.repository import TransactionRepository
from account_service.service import AccountServiceLogic

logger = setup_logger("account_service")
router = APIRouter()

@router.get("/health", response_model=APIResponse)
def health_check():
    return APIResponse(success=True, data={"status": "up", "service": "account_service"})

def get_account_service(db: Session = Depends(get_db)):
    repo = TransactionRepository(db)
    return AccountServiceLogic(repo)

@router.post("/accounts/{account_id}/transactions", status_code=HTTPStatus.CREATED, response_model=APIResponse)
def apply_transaction(account_id: str, payload: EventPayload, svc: AccountServiceLogic = Depends(get_account_service)):
    trace_id = trace_id_ctx_var.get()
    
    if payload.accountId != account_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Account ID in path must match payload")

    result = svc.process_transaction(
        event_id=payload.eventId,
        account_id=account_id,
        tx_type=payload.type,
        amount=payload.amount,
        currency=payload.currency,
        event_time=payload.eventTimestamp
    )
    
    if result["status"] == "duplicate":
        logger.info(f"Duplicate event {payload.eventId} received, ignoring.")
    else:
        logger.info(f"Applied transaction {payload.eventId} to account {account_id}")
        
    return APIResponse(success=True, data=result, trace_id=trace_id)

@router.get("/accounts/{account_id}/balance", response_model=APIResponse)
def get_balance(account_id: str, svc: AccountServiceLogic = Depends(get_account_service)):
    trace_id = trace_id_ctx_var.get()
    balance = svc.calculate_balance(account_id)
    logger.info(f"Calculated balance for account {account_id}")
    return APIResponse(success=True, data={"accountId": account_id, "balance": balance}, trace_id=trace_id)

@router.get("/accounts/{account_id}", response_model=APIResponse)
def get_account_details(account_id: str, svc: AccountServiceLogic = Depends(get_account_service)):
    trace_id = trace_id_ctx_var.get()
    details = svc.get_account_details(account_id)
    logger.info(f"Retrieved account details for {account_id}")
    return APIResponse(success=True, data=details, trace_id=trace_id)
