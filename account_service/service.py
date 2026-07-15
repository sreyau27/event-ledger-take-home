from datetime import datetime
from account_service.repository import TransactionRepository

class AccountServiceLogic:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def process_transaction(self, event_id: str, account_id: str, tx_type: str, amount: float, currency: str, event_time: datetime):
        tx, created = self.repo.create(
            event_id=event_id,
            account_id=account_id,
            tx_type=tx_type,
            amount=amount,
            currency=currency,
            event_timestamp=event_time
        )
        
        if not created:
            return {"status": "duplicate", "eventId": event_id}
            
        return {"status": "success", "eventId": event_id}

    def calculate_balance(self, account_id: str) -> float:
        transactions = self.repo.get_by_account_id(account_id)
        balance = 0.0
        for tx in transactions:
            if tx.type == "CREDIT":
                balance += tx.amount
            elif tx.type == "DEBIT":
                balance -= tx.amount
        return balance

    def get_account_details(self, account_id: str):
        balance = self.calculate_balance(account_id)
        recent_txs = self.repo.get_by_account_id(account_id, limit=10, order_by_desc=False)
        
        return {
            "accountId": account_id,
            "balance": balance,
            "recentTransactions": [
                {
                    "eventId": tx.event_id,
                    "type": tx.type,
                    "amount": tx.amount,
                    "currency": tx.currency,
                    "eventTimestamp": tx.event_timestamp.isoformat()
                } for tx in recent_txs
            ]
        }
