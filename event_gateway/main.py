from fastapi import FastAPI, Request
import uuid
from shared.logging import setup_logger, trace_id_ctx_var
from event_gateway.database import init_db
from event_gateway.handler import router as gateway_router
from event_gateway.handler import http_client

logger = setup_logger("event_gateway")

app = FastAPI(title="Event Gateway API")

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Event Gateway started and DB initialized.")

@app.on_event("shutdown")
async def on_shutdown():
    await http_client.aclose()

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
