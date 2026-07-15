from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from shared.schemas import EventPayload
from shared.logging import setup_logger
from account_service.database import get_db
from account_service.repository import TransactionRepository
from account_service.service import AccountServiceLogic

logger = setup_logger("account_service")
router = APIRouter()

def get_account_service(db: Session = Depends(get_db)):
    repo = TransactionRepository(db)
    return AccountServiceLogic(repo)

@router.post("/accounts/{account_id}/transactions", status_code=201)
def apply_transaction(account_id: str, payload: EventPayload, svc: AccountServiceLogic = Depends(get_account_service)):
    if payload.accountId != account_id:
        raise HTTPException(status_code=400, detail="Account ID in path must match payload")

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
        
    return result

@router.get("/accounts/{account_id}/balance")
def get_balance(account_id: str, svc: AccountServiceLogic = Depends(get_account_service)):
    balance = svc.calculate_balance(account_id)
    logger.info(f"Calculated balance for account {account_id}")
    return {"accountId": account_id, "balance": balance}

@router.get("/accounts/{account_id}")
def get_account_details(account_id: str, svc: AccountServiceLogic = Depends(get_account_service)):
    details = svc.get_account_details(account_id)
    logger.info(f"Retrieved account details for {account_id}")
    return details
