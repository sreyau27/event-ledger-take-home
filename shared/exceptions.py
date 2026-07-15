from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from shared.logging import setup_logger, trace_id_ctx_var
import traceback

logger = setup_logger("global_exception_handler")

class AccountServiceUnavailable(Exception):
    pass

def add_global_exception_handlers(app: FastAPI):
    @app.exception_handler(AccountServiceUnavailable)
    async def account_service_unavailable_handler(request: Request, exc: AccountServiceUnavailable):
        trace_id = trace_id_ctx_var.get()
        logger.error(f"Account service is currently unavailable. Circuit breaker open / retries exhausted.")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "data": None,
                "error": "Service Unavailable",
                "message": "Account Service is down",
                "trace_id": trace_id
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = trace_id_ctx_var.get()
        logger.error(f"Validation error: {exc.errors()} | body: {exc.body}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "success": False,
                "data": None,
                "error": "Validation Error",
                "message": jsonable_encoder(exc.errors()),
                "trace_id": trace_id
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        trace_id = trace_id_ctx_var.get()
        logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "data": None,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred.",
                "trace_id": trace_id
            },
        )
