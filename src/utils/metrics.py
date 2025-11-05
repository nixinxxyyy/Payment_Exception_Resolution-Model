"""
Metrics tracking for the ticket management system.
"""

import logging
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)


class TicketMetrics:
    """
    Track and calculate performance metrics for the ticket system.

    Metrics include:
    - Total tickets processed
    - Escalation rate
    - Automation rate
    - Category distribution
    - Average response time
    """

    def __init__(self):
        """Initialize metrics tracker."""
        self.total_tickets = 0
        self.escalated_tickets = 0
        self.category_counts = defaultdict(int)
        self.response_times = []
        logger.info("Metrics tracker initialized")

    def record_ticket(self, category: str, escalated: bool, response_time: float):
        """
        Record metrics for a processed ticket.

        Args:
            category: Ticket category (TECHNICAL, BILLING, GENERAL)
            escalated: Whether ticket was escalated to human
            response_time: Processing time in seconds
        """
        self.total_tickets += 1
        self.category_counts[category] += 1
        self.response_times.append(response_time)

        if escalated:
            self.escalated_tickets += 1

        logger.debug(f"Recorded metrics - Total: {self.total_tickets}, Escalated: {self.escalated_tickets}")

    def get_metrics(self) -> Dict:
        """
        Get current system metrics.

        Returns:
            Dictionary containing all metrics
        """
        automation_rate = 0.0
        if self.total_tickets > 0:
            automation_rate = ((self.total_tickets - self.escalated_tickets) / self.total_tickets) * 100

        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)

        return {
            "total_tickets": self.total_tickets,
            "escalated_tickets": self.escalated_tickets,
            "automated_tickets": self.total_tickets - self.escalated_tickets,
            "automation_rate": round(automation_rate, 2),
            "escalation_rate": round(100 - automation_rate, 2),
            "average_response_time": round(avg_response_time, 2),
            "category_distribution": dict(self.category_counts),
            "min_response_time": round(min(self.response_times), 2) if self.response_times else 0,
            "max_response_time": round(max(self.response_times), 2) if self.response_times else 0,
        }

    def reset(self):
        """Reset all metrics."""
        self.total_tickets = 0
        self.escalated_tickets = 0
        self.category_counts = defaultdict(int)
        self.response_times = []
        logger.info("Metrics reset")

    def __str__(self) -> str:
        """String representation of metrics."""
        metrics = self.get_metrics()
        return (
            f"Tickets: {metrics['total_tickets']} | "
            f"Automated: {metrics['automation_rate']}% | "
            f"Avg Time: {metrics['average_response_time']}s"
        )
