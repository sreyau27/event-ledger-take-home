from fastapi import FastAPI, Request
from shared.logging import setup_logger, trace_id_ctx_var
from account_service.database import init_db
from account_service.handler import router as account_router
from shared.exceptions import add_global_exception_handlers
from contextlib import asynccontextmanager

logger = setup_logger("account_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Account Service started and DB initialized.")
    yield

app = FastAPI(title="Account Service", lifespan=lifespan)
add_global_exception_handlers(app)

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", "")
    trace_id_ctx_var.set(trace_id)
    response = await call_next(request)
    return response


