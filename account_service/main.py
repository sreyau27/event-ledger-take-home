from fastapi import FastAPI, Request
from shared.logging import setup_logger, trace_id_ctx_var
from account_service.database import init_db
from account_service.handler import router as account_router

from contextlib import asynccontextmanager

logger = setup_logger("account_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Account Service started and DB initialized.")
    yield

app = FastAPI(title="Account Service", lifespan=lifespan)

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", "")
    trace_id_ctx_var.set(trace_id)
    response = await call_next(request)
    return response

@app.get("/health")
def health_check():
    return {"status": "up", "service": "account_service"}

app.include_router(account_router)
