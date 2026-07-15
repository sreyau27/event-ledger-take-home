import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from event_gateway.database import Base
from event_gateway.repository import EventRepository

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
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    return EventRepository(db_session)

def test_create_and_get_by_event_id(repo):
    dt = datetime.now(timezone.utc)
    repo.create("evt-1", "acc-1", '{"type": "CREDIT"}', dt, dt)
    
    event = repo.get_by_event_id("evt-1")
    assert event is not None
    assert event.event_id == "evt-1"
    assert event.account_id == "acc-1"
    assert event.payload_json == '{"type": "CREDIT"}'

def test_list_events(repo):
    dt = datetime.now(timezone.utc)
    repo.create("evt-1", "acc-1", '{"type": "CREDIT"}', dt, dt)
    repo.create("evt-2", "acc-1", '{"type": "DEBIT"}', dt, dt)
    repo.create("evt-3", "acc-2", '{"type": "CREDIT"}', dt, dt)
    
    events = repo.get_by_account_id("acc-1")
    assert len(events) == 2
    assert {e.event_id for e in events} == {"evt-1", "evt-2"}
