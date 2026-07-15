from fastapi import FastAPI, Request
import uuid
from shared.logging import setup_logger, trace_id_ctx_var
from event_gateway.database import init_db
from event_gateway.handler import router as gateway_router
from event_gateway.handler import http_client
from shared.exceptions import add_global_exception_handlers

from contextlib import asynccontextmanager

logger = setup_logger("event_gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Event Gateway started and DB initialized.")
    yield
    await http_client.aclose()

app = FastAPI(title="Event Gateway API", lifespan=lifespan)
add_global_exception_handlers(app)

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        trace_id = str(uuid.uuid4())
    trace_id_ctx_var.set(trace_id)
    
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response

@app.get("/health")
def health_check():
    return {"status": "up", "service": "event_gateway"}

app.include_router(gateway_router)
