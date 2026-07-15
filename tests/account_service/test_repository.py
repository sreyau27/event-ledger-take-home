import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from account_service.database import Base
from account_service.repository import TransactionRepository

@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    
@pytest.fixture
def repo(db_session):
    # clear db
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    return TransactionRepository(db_session)

def test_create_and_get_by_event_id(repo):
    dt = datetime.now(timezone.utc)
    repo.create("evt-1", "acc-1", "CREDIT", 100.0, "USD", dt)
    
    tx = repo.get_by_event_id("evt-1")
    assert tx is not None
    assert tx.account_id == "acc-1"
    assert tx.type == "CREDIT"
    assert tx.amount == 100.0
    
    assert repo.get_by_event_id("evt-nonexistent") is None

def test_get_by_account_id(repo):
    base_dt = datetime.now(timezone.utc)
    repo.create("evt-1", "acc-1", "CREDIT", 100.0, "USD", base_dt)
    repo.create("evt-2", "acc-1", "DEBIT", 50.0, "USD", base_dt + timedelta(minutes=1))
    repo.create("evt-3", "acc-2", "CREDIT", 200.0, "USD", base_dt + timedelta(minutes=2))
    
    txs = repo.get_by_account_id("acc-1")
    assert len(txs) == 2
    assert {tx.event_id for tx in txs} == {"evt-1", "evt-2"}

def test_get_by_account_id_order_and_limit(repo):
    base_dt = datetime.now(timezone.utc)
    repo.create("evt-1", "acc-1", "CREDIT", 10.0, "USD", base_dt)
    repo.create("evt-2", "acc-1", "CREDIT", 20.0, "USD", base_dt + timedelta(minutes=1))
    repo.create("evt-3", "acc-1", "CREDIT", 30.0, "USD", base_dt + timedelta(minutes=2))
    
    txs = repo.get_by_account_id("acc-1", limit=2, order_by_desc=True)
    assert len(txs) == 2
    assert txs[0].event_id == "evt-3"
    assert txs[1].event_id == "evt-2"
