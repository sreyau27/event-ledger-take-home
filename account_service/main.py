from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from shared.schemas import EventPayload
from shared.logging import setup_logger, trace_id_ctx_var
from account_service.database import init_db, get_db
from account_service.models import Transaction

logger = setup_logger("account_service")

app = FastAPI(title="Account Service")

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Account Service started and DB initialized.")

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", "")
    trace_id_ctx_var.set(trace_id)
    response = await call_next(request)
    return response

@app.get("/health")
def health_check():
    return {"status": "up", "service": "account_service"}

@app.post("/accounts/{account_id}/transactions", status_code=201)
def apply_transaction(account_id: str, payload: EventPayload, db: Session = Depends(get_db)):
    if payload.accountId != account_id:
        raise HTTPException(status_code=400, detail="Account ID in path must match payload")

    # Check for duplicate event
    existing_tx = db.query(Transaction).filter(Transaction.event_id == payload.eventId).first()
    if existing_tx:
        logger.info(f"Duplicate event {payload.eventId} received, ignoring.")
        # Return 200 OK since it was already processed
        return {"status": "duplicate", "eventId": payload.eventId}
        
    try:
        # Handle 'Z' suffix for UTC in ISO 8601
        ts = payload.eventTimestamp.replace("Z", "+00:00")
        event_time = datetime.fromisoformat(ts)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid eventTimestamp format")

    new_tx = Transaction(
        event_id=payload.eventId,
        account_id=account_id,
        type=payload.type,
        amount=payload.amount,
        currency=payload.currency,
        event_timestamp=event_time
    )
    db.add(new_tx)
    db.commit()
    logger.info(f"Applied transaction {payload.eventId} to account {account_id}")
    return {"status": "success", "eventId": payload.eventId}

@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: str, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.account_id == account_id).all()
    
    balance = 0.0
    for tx in transactions:
        if tx.type == "CREDIT":
            balance += tx.amount
        elif tx.type == "DEBIT":
            balance -= tx.amount
            
    logger.info(f"Calculated balance for account {account_id}")
    return {"accountId": account_id, "balance": balance}

@app.get("/accounts/{account_id}")
def get_account_details(account_id: str, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.account_id == account_id).order_by(Transaction.event_timestamp.desc()).all()
    
    balance = 0.0
    recent_txs = []
    
    for tx in db.query(Transaction).filter(Transaction.account_id == account_id).all():
        if tx.type == "CREDIT":
            balance += tx.amount
        elif tx.type == "DEBIT":
            balance -= tx.amount
            
    for tx in transactions[:10]:
        recent_txs.append({
            "eventId": tx.event_id,
            "type": tx.type,
            "amount": tx.amount,
            "currency": tx.currency,
            "eventTimestamp": tx.event_timestamp.isoformat()
        })
        
    logger.info(f"Retrieved account details for {account_id}")
    return {
        "accountId": account_id,
        "balance": balance,
        "recentTransactions": recent_txs
    }
