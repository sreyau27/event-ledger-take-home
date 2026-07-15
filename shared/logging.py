import logging
import json
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variable to store trace ID
trace_id_ctx_var: ContextVar[str] = ContextVar("trace_id", default="")

class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
            "trace_id": trace_id_ctx_var.get()
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(service_name: str):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter(service_name))
        logger.addHandler(handler)
        
    return logger
