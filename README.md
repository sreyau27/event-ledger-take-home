# Event Ledger

This repository contains the solution for the Event Ledger take-home project. It implements a resilient distributed system composed of two microservices that process financial transaction events.

## Architecture Overview

The system consists of two independently runnable microservices:

1. **Event Gateway API (public-facing)**: The entry point for all client requests. It receives transaction events, validates the payload, enforces idempotency, stores event records, and communicates synchronously with the Account Service.
2. **Account Service (internal)**: Manages account states, including computing balances and storing transaction history. It is only called by the Event Gateway and is not exposed to external clients.

Both services are built using Python and use their own independent **in-memory SQLite databases**. There are no external database dependencies or Alembic migrations required to run this project.

### N-Tier Application Structure
To promote separation of concerns, both microservices follow a strict **N-Tier Architecture**:
- `main.py`: Fast API application setup, middleware (e.g. trace ID propagation), and lifecycle events.
- `handler.py`: Presentation layer containing HTTP routes, endpoint definitions, and dependency injection.
- `service.py`: Business logic layer (computations, validations, idempotency logic, and downstream communication).
- `repository.py`: Data access layer dealing strictly with database operations.
- `database.py`: SQLAlchemy session and declarative base setup.

### Unified API Response Format
All endpoints across the system adhere to a single, standardized JSON response structure (`APIResponse`), regardless of success or failure. This simplifies client consumption:

**Success Response Example:**
```json
{
  "success": true,
  "data": { "eventId": "evt-123" },
  "error": null,
  "message": null,
  "trace_id": "4b9287a5-4f76-4d2c-80a2-23c2a9341457"
}
```

**Error Response Example:**
```json
{
  "success": false,
  "data": null,
  "error": "Service Unavailable",
  "message": "Account Service is down",
  "trace_id": "4b9287a5-4f76-4d2c-80a2-23c2a9341457"
}
```

## Setup Instructions

### Prerequisites
- Python 3.9+ 
- `pip` (Python package manager)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd event-ledger-take-home
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Since we use in-memory SQLite, there is no database setup or Alembic migration step needed!)*

## Running the Services

You can run the services manually. Make sure your virtual environment is activated.

### 1. Start the Account Service (Internal)
In a new terminal window:
```bash
# Starts on port 8001
uvicorn account_service.main:app --port 8001 --reload
```

### 2. Start the Event Gateway API (Public)
In another terminal window:
```bash
# Starts on port 8000
uvicorn event_gateway.main:app --port 8000 --reload
```

## Running the Tests

The project includes an extensive, modular test suite with **31 test cases** achieving high coverage across schemas, global exceptions, repositories, services, and handlers. The tests are logically segregated to mirror the main application structure:
- `tests/shared/`
- `tests/account_service/`
- `tests/event_gateway/`

To run the entire test suite, simply execute:
```bash
python -m pytest
```

## Resiliency Pattern

The Event Gateway implements a **Circuit Breaker** (combined with timeout and retries) for its synchronous calls to the Account Service via the `tenacity` library. 

**Why this choice?** 
In a distributed system, if the downstream Account Service experiences degradation or goes offline, continuing to send requests would exhaust the Gateway's resources and lead to cascading failures. The retry logic automatically mitigates transient network issues, while the global exception handlers safely wrap exhausted failures into a clean 503 response.

Additionally, graceful degradation is implemented so that read-only `GET` endpoints for events continue to serve data from the Gateway's local in-memory store even if the Account Service is completely unreachable.
