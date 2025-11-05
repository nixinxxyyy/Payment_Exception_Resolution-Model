# API Reference

Complete API documentation for the Customer Support Ticket Management System.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement API key or OAuth2 authentication.

---

## Endpoints

### 1. Root Endpoint

Get API information and available endpoints.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "Customer Support Ticket Management System API",
  "version": "1.0.0",
  "endpoints": {
    "process_ticket": "/api/v1/tickets/process",
    "health": "/health",
    "metrics": "/api/v1/metrics"
  }
}
```

**Status Codes:**
- `200 OK`: Success

**Example:**
```bash
curl http://localhost:8000/
```

---

### 2. Health Check

Check the API health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00.000000"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 3. Process Ticket

Process a customer support ticket through the multi-agent system.

**Endpoint:** `POST /api/v1/tickets/process`

**Request Body:**
```json
{
  "customer_query": "string (required)",
  "customer_email": "string (optional)",
  "ticket_id": "string (optional)"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| customer_query | string | Yes | The customer's support question or issue |
| customer_email | string | No | Customer's email address |
| ticket_id | string | No | Custom ticket ID (auto-generated if not provided) |

**Response:**
```json
{
  "ticket_id": "TKT-ABC12345",
  "category": "TECHNICAL",
  "final_response": "Thank you for reaching out to our support team...",
  "needs_escalation": false,
  "priority": "medium",
  "timestamp": "2025-01-15T10:30:00.000000",
  "conversation_history": [
    "[INTAKE] Customer reports application crash...",
    "[FAQ] No direct match found",
    "[CLASSIFIER] Category: TECHNICAL",
    "[TECHNICAL] Resolution provided",
    "[ESCALATION] Cleared for automated response",
    "[RESPONSE] Final response generated"
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| ticket_id | string | Unique ticket identifier |
| category | string | Ticket category (TECHNICAL/BILLING/GENERAL) |
| final_response | string | Customer-facing response |
| needs_escalation | boolean | Whether ticket needs human review |
| priority | string | Priority level (low/medium/high) |
| timestamp | string | ISO 8601 timestamp |
| conversation_history | array | Log of agent interactions (optional) |

**Status Codes:**
- `200 OK`: Ticket processed successfully
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Processing error

**Examples:**

**Technical Issue:**
```bash
curl -X POST "http://localhost:8000/api/v1/tickets/process" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_query": "My application crashes when uploading files over 10MB",
    "customer_email": "user@example.com"
  }'
```

**Billing Issue:**
```bash
curl -X POST "http://localhost:8000/api/v1/tickets/process" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_query": "I was charged twice for my subscription",
    "customer_email": "customer@example.com"
  }'
```

**General Question:**
```bash
curl -X POST "http://localhost:8000/api/v1/tickets/process" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_query": "How do I reset my password?"
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/tickets/process",
    json={
        "customer_query": "My app keeps crashing",
        "customer_email": "user@example.com"
    }
)

data = response.json()
print(f"Ticket ID: {data['ticket_id']}")
print(f"Category: {data['category']}")
print(f"Response: {data['final_response']}")
```

---

### 4. Get Metrics

Retrieve system performance metrics.

**Endpoint:** `GET /api/v1/metrics`

**Response:**
```json
{
  "total_tickets": 150,
  "escalated_tickets": 30,
  "automated_tickets": 120,
  "automation_rate": 80.0,
  "escalation_rate": 20.0,
  "average_response_time": 3.5,
  "category_distribution": {
    "TECHNICAL": 60,
    "BILLING": 45,
    "GENERAL": 45
  },
  "min_response_time": 2.1,
  "max_response_time": 8.3
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| total_tickets | integer | Total tickets processed |
| escalated_tickets | integer | Tickets escalated to humans |
| automated_tickets | integer | Tickets auto-resolved |
| automation_rate | float | Percentage of auto-resolved tickets |
| escalation_rate | float | Percentage of escalated tickets |
| average_response_time | float | Average processing time (seconds) |
| category_distribution | object | Count by category |
| min_response_time | float | Fastest processing time |
| max_response_time | float | Slowest processing time |

**Status Codes:**
- `200 OK`: Metrics retrieved successfully
- `500 Internal Server Error`: Error retrieving metrics

**Example:**
```bash
curl http://localhost:8000/api/v1/metrics
```

**Python Example:**
```python
import requests

response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()

print(f"Automation Rate: {metrics['automation_rate']}%")
print(f"Average Response Time: {metrics['average_response_time']}s")
```

---

### 5. Reset Metrics

Reset all system metrics (useful for testing).

**Endpoint:** `POST /api/v1/metrics/reset`

**Response:**
```json
{
  "message": "Metrics reset successfully"
}
```

**Status Codes:**
- `200 OK`: Metrics reset successfully
- `500 Internal Server Error`: Error resetting metrics

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/metrics/reset
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Status Codes:**

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server-side error |

---

## Interactive Documentation

The API provides interactive documentation using Swagger UI and ReDoc:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Explore all endpoints
- View request/response schemas
- Test API calls directly from the browser
- Download OpenAPI specification

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider implementing:
- Request rate limits per IP
- Token bucket algorithm
- Burst protection
- 429 Too Many Requests responses

---

## CORS Configuration

The API currently allows requests from all origins (`allow_origins=["*"]`).

For production, configure specific allowed origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Best Practices

### 1. Error Handling
Always check response status codes and handle errors appropriately.

### 2. Timeout Settings
Set reasonable timeout values for API requests:
```python
response = requests.post(url, json=data, timeout=30)
```

### 3. Retry Logic
Implement exponential backoff for failed requests:
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
```

### 4. Request Validation
Validate input before sending to API to avoid 422 errors.

### 5. Logging
Log all API interactions for debugging and monitoring.

---

## Versioning

The API uses URL versioning (`/api/v1/`). Future versions will be available at `/api/v2/`, etc.

---

## Support

For API support:
- Check `/docs` for interactive documentation
- Review this reference guide
- Check application logs at `logs/ticket_system.log`
- Create an issue on GitHub

---

## Changelog

### v1.0.0 (2025-01-15)
- Initial API release
- Process ticket endpoint
- Metrics endpoint
- Health check endpoint
