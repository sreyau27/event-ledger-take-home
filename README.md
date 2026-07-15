# Event Ledger

This repository contains the solution for the Event Ledger take-home project. It implements a resilient distributed system composed of two microservices that process financial transaction events.

## Architecture Overview

The system consists of two independently runnable microservices:

1. **Event Gateway API (public-facing)**: The entry point for all client requests. It receives transaction events, validates the payload, enforces idempotency, stores event records, and communicates synchronously with the Account Service.
2. **Account Service (internal)**: Manages account states, including computing balances and storing transaction history. It is only called by the Event Gateway and is not exposed to external clients.

Both services are built using Python and use their own independent **in-memory SQLite databases**. There are no external database dependencies or Alembic migrations required to run this project.

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

*(Alternatively, if a `docker-compose.yml` is provided, you can start both services using `docker-compose up`)*

## Running the Tests

The project includes an automated test suite covering core functionality (idempotency, out-of-order processing, validation), resiliency behavior, and trace propagation.

To run the tests, simply execute:
```bash
pytest
```

## Resiliency Pattern

The Event Gateway implements a **Circuit Breaker** (combined with timeout and retries) for its synchronous calls to the Account Service. 

**Why this choice?** 
In a distributed system, if the downstream Account Service experiences degradation or goes offline, continuing to send requests would exhaust the Gateway's resources and lead to cascading failures. The Circuit Breaker pattern detects repeated failures and "opens" the circuit, returning a meaningful error (e.g., `503 Service Unavailable`) to the client quickly without hanging. 

Additionally, graceful degradation is implemented so that read-only `GET` endpoints for events continue to serve data from the Gateway's local in-memory store even if the Account Service is completely unreachable.
