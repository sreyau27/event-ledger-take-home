from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from account_service.models import Transaction

class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_by_event_id(self, event_id: str):
        return self.db.query(Transaction).filter(Transaction.event_id == event_id).first()
        
    def get_by_account_id(self, account_id: str, limit: int = None, order_by_desc: bool = False):
        query = self.db.query(Transaction).filter(Transaction.account_id == account_id)
        if order_by_desc:
            query = query.order_by(Transaction.event_timestamp.desc())
        else:
            query = query.order_by(Transaction.event_timestamp.asc())
        if limit:
            query = query.limit(limit)
        return query.all()
        
    def create(self, event_id: str, account_id: str, tx_type: str, amount: float, currency: str, event_timestamp: datetime):
        new_tx = Transaction(
            event_id=event_id,
            account_id=account_id,
            type=tx_type,
            amount=amount,
            currency=currency,
            event_timestamp=event_timestamp
        )
        try:
            self.db.add(new_tx)
            self.db.commit()
            return new_tx, True
        except IntegrityError:
            self.db.rollback()
            return self.get_by_event_id(event_id), False
