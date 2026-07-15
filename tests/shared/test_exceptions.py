import pytest
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from shared.exceptions import add_global_exception_handlers, AccountServiceUnavailable
from pydantic import BaseModel

app = FastAPI()
add_global_exception_handlers(app)
router = APIRouter()

class DummyPayload(BaseModel):
    name: str

@router.get("/error/service-unavailable")
def trigger_service_unavailable():
    raise AccountServiceUnavailable("Test Down")

@router.post("/error/validation")
def trigger_validation(payload: DummyPayload):
    return payload

@router.get("/error/unhandled")
def trigger_unhandled():
    raise Exception("Boom!")

app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)

def test_account_service_unavailable_handler():
    response = client.get("/error/service-unavailable")
    assert response.status_code == 503
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error"] == "Service Unavailable"
    assert json_resp["message"] == "Account Service is down"

def test_validation_exception_handler():
    response = client.post("/error/validation", json={"wrong_key": "val"})
    assert response.status_code == 422
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error"] == "Validation Error"
    assert isinstance(json_resp["message"], list)

def test_global_exception_handler():
    response = client.get("/error/unhandled")
    assert response.status_code == 500
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error"] == "Internal Server Error"
