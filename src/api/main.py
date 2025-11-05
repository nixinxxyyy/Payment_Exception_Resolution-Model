"""
FastAPI REST API for the Customer Support Ticket Management System.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

from src.workflow import app as workflow_app
from src.config import config
from src.utils.logger import setup_logging
from src.utils.metrics import TicketMetrics

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
api_app = FastAPI(
    title="Customer Support Ticket Management System",
    description="Multi-Agent AI System for automating customer support ticket processing",
    version="1.0.0"
)

# Add CORS middleware
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize metrics tracker
metrics = TicketMetrics()


# Request/Response Models
class TicketRequest(BaseModel):
    """Request model for ticket submission."""
    customer_query: str = Field(..., description="Customer's support query")
    customer_email: Optional[str] = Field(None, description="Customer email address")
    ticket_id: Optional[str] = Field(None, description="Optional custom ticket ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_query": "My application crashes when I try to upload large files",
                "customer_email": "customer@example.com"
            }
        }
    )


class TicketResponse(BaseModel):
    """Response model for processed ticket."""
    ticket_id: str
    category: str
    final_response: str
    needs_escalation: bool
    priority: str
    timestamp: str
    conversation_history: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    total_tickets: int
    escalated_tickets: int
    automation_rate: float
    average_response_time: float
    category_distribution: dict


# API Endpoints

@api_app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Customer Support Ticket Management System API",
        "version": "1.0.0",
        "endpoints": {
            "process_ticket": "/api/v1/tickets/process",
            "health": "/health",
            "metrics": "/api/v1/metrics"
        }
    }


@api_app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@api_app.post("/api/v1/tickets/process", response_model=TicketResponse)
async def process_ticket(request: TicketRequest):
    """
    Process a customer support ticket through the multi-agent system.

    Args:
        request: Ticket request containing customer query

    Returns:
        Processed ticket with resolution or escalation status
    """
    try:
        # Generate ticket ID if not provided
        ticket_id = request.ticket_id or f"{config.TICKET_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"

        logger.info(f"Processing new ticket: {ticket_id}")

        # Create initial state
        initial_state = {
            "customer_query": request.customer_query,
            "ticket_id": ticket_id,
            "category": "",
            "faq_match": "",
            "resolution": "",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": [],
            "customer_email": request.customer_email,
            "priority": "medium",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        # Start metrics tracking
        start_time = datetime.now()

        # Process ticket through workflow
        result = workflow_app.invoke(initial_state)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        # Update metrics
        metrics.record_ticket(
            category=result["category"],
            escalated=result["needs_escalation"],
            response_time=processing_time
        )

        logger.info(
            f"Ticket {ticket_id} processed - "
            f"Category: {result['category']}, "
            f"Escalated: {result['needs_escalation']}, "
            f"Time: {processing_time:.2f}s"
        )

        # Return response
        return TicketResponse(
            ticket_id=result["ticket_id"],
            category=result["category"],
            final_response=result["final_response"],
            needs_escalation=result["needs_escalation"],
            priority=result["priority"],
            timestamp=result["timestamp"],
            conversation_history=result["conversation_history"]
        )

    except Exception as e:
        logger.error(f"Error processing ticket: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ticket: {str(e)}"
        )


@api_app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get system performance metrics.

    Returns:
        Current system metrics including automation rate and performance stats
    """
    try:
        metrics_data = metrics.get_metrics()

        return MetricsResponse(
            total_tickets=metrics_data["total_tickets"],
            escalated_tickets=metrics_data["escalated_tickets"],
            automation_rate=metrics_data["automation_rate"],
            average_response_time=metrics_data["average_response_time"],
            category_distribution=metrics_data["category_distribution"]
        )

    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metrics: {str(e)}"
        )


@api_app.post("/api/v1/metrics/reset")
async def reset_metrics():
    """Reset all metrics (useful for testing)."""
    try:
        metrics.reset()
        logger.info("Metrics reset")
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting metrics: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Validate configuration
    config.validate()

    # Run the API server
    uvicorn.run(
        "src.api.main:api_app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
