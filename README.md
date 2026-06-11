# Payment Exception Resolution Agent

**A Production-Grade Multi-Agent AI System for Diagnosing, Routing, and Resolving Failed Banking Payment Transactions**

---

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         Payment Exception Input       │
                    │  payment_id · client_id · amount      │
                    │  payment_rail · failure_code · ...    │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │         INGESTION AGENT              │
                    │  Validate · Normalise · Deduplicate  │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │       INVESTIGATION AGENT            │
                    │  Balance · Beneficiary · Network     │
                    │  Compliance · Cut-off · Retries      │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │      ROOT CAUSE ANALYSIS AGENT       │
                    │  GPT-4o diagnoses failure type       │
                    │  Determines automation safety        │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │          DECISION AGENT              │
                    │  Rule-based + LLM resolution choice  │
                    │  Safety override for ambiguous cases │
                    └──────┬──────────────────────────────┘
                           │
          ┌────────────────┼──────────────────────────────┐
          │                │                │              │
    AUTO_RETRY       CLIENT_OUTREACH  COMPLIANCE    MANUAL_REVIEW
    AUTO_CORRECT     ┌─────┐          REVIEW        CANCEL
    DUPLICATE_SUPP   │ 📧  │          ┌─────┐       ┌─────┐
    HOLD_FOR_WINDOW  │     │          │ 🛡️  │       │ 👤  │
    ┌────────┐       └──┬──┘          └──┬──┘       └──┬──┘
    │  🤖   │          │                 │              │
    └───┬───┘          │                 │              │
        │              └─────────────────┴──────────────┘
        │                                │
        └────────────────────────────────┘
                           │
                    ┌──────▼──────────────────────────────┐
                    │           EGRESS AGENT               │
                    │  Persist to MySQL · Deliver outputs  │
                    │  Seal audit trail · Emit metrics     │
                    └─────────────────────────────────────┘
```

## Agent Catalogue

| Agent | Purpose | Authority |
|---|---|---|
| **Ingestion Agent** | Validate, normalise, deduplicate exceptions | Accept/reject input |
| **Investigation Agent** | Gather balance, beneficiary, network, compliance evidence | Read-only data access |
| **Root Cause Agent** | GPT-4o diagnoses failure type and safety | Diagnose only |
| **Decision Agent** | Choose resolution action (rules + LLM) | Decide only |
| **Auto-Resolve Agent** | Execute AUTO_RETRY, AUTO_CORRECT, HOLD, SUPPRESS | Write to payment gateway |
| **Client Outreach Agent** | Generate and queue client notifications | Write to notification service |
| **Compliance Agent** | Escalate to compliance/AML queue | Escalate + lock |
| **Manual Review Agent** | Package case for ops team | Assign + lock |
| **Egress Agent** | Persist to MySQL, seal audit trail | Write DB |

## Failure Types Handled

| Failure Type | Resolution Path |
|---|---|
| `INSUFFICIENT_FUNDS` | CLIENT_OUTREACH |
| `INCORRECT_BENEFICIARY` | AUTO_CORRECT (minor) / CLIENT_OUTREACH (major) |
| `DUPLICATE_PAYMENT` | DUPLICATE_SUPPRESS |
| `COMPLIANCE_HOLD` | COMPLIANCE_REVIEW (locked) |
| `NETWORK_RAIL_FAILURE` | AUTO_RETRY (if UP) / HOLD_FOR_WINDOW (if DOWN) |
| `CUTOFF_TIME_MISS` | HOLD_FOR_WINDOW (next rail cycle) |
| `UNCERTAIN_RETRY_STATUS` | MANUAL_REVIEW |

## Tech Stack

- **Orchestration**: LangGraph (StateGraph)
- **LLM**: OpenAI GPT-4o via LangChain
- **Backend API**: FastAPI + Uvicorn
- **Database**: MySQL via SQLAlchemy + PyMySQL
- **Frontend**: React + Vite + Recharts (banking UI)

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- MySQL 8.0+
- Node.js 18+
- OpenAI API key

### 2. Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY, DB_PASSWORD, etc.
```

### 4. Set up MySQL database

```bash
python scripts/setup_database.py
```

### 5. Start the backend API

```bash
uvicorn src.api.main:api_app --reload --port 8000
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 7. Run end-to-end demo

```bash
python scripts/run_example.py
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/exceptions/submit` | Submit new payment exception |
| `GET` | `/api/v1/exceptions/{id}` | Get exception details + audit trail |
| `GET` | `/api/v1/exceptions` | List exceptions (filterable) |
| `POST` | `/api/v1/exceptions/{id}/replay` | Replay with new status event |
| `POST` | `/api/v1/exceptions/{id}/override` | Operator override with justification |
| `GET` | `/api/v1/metrics` | System performance metrics |
| `GET` | `/health` | Health check with DB status |

---

## Production-Grade Features

- **Idempotency**: Duplicate exception events detected and suppressed
- **Auditability**: Immutable audit trail per exception in MySQL
- **Safety controls**: Automated actions blocked unless `is_safe_to_automate=True`
- **Feedback loop**: `/replay` endpoint re-evaluates on new status events
- **Operator override**: Ops can override any decision with mandatory justification
- **Configurability**: All thresholds, rail cut-offs, retry limits via `.env`
- **Observability**: Structured logs, in-memory metrics, DB persistence
- **Determinism**: Rule-based decision layer; LLM only for ambiguous cases
