"""
Metrics tracking for the Payment Exception Resolution system.
Tracks in-memory counters; persisted stats are in MySQL.
"""

import logging
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)


class ExceptionMetrics:
    """Track performance metrics for the payment exception resolution system."""

    def __init__(self):
        self.total_exceptions       = 0
        self.escalated_exceptions   = 0
        self.auto_resolved          = 0
        self.failure_type_counts    = defaultdict(int)
        self.resolution_counts      = defaultdict(int)
        self.response_times         = []
        logger.info("ExceptionMetrics tracker initialised.")

    def record_exception(
        self,
        failure_type: str,
        resolution_action: str,
        escalated: bool,
        response_time: float,
    ):
        self.total_exceptions += 1
        self.failure_type_counts[failure_type] += 1
        self.resolution_counts[resolution_action] += 1
        self.response_times.append(response_time)
        if escalated:
            self.escalated_exceptions += 1
        else:
            self.auto_resolved += 1

    def get_metrics(self) -> Dict:
        total = self.total_exceptions or 1   # avoid div-by-zero
        avg_rt = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0.0
        )
        return {
            "total_exceptions":         self.total_exceptions,
            "escalated_exceptions":     self.escalated_exceptions,
            "auto_resolved":            self.auto_resolved,
            "automation_rate_pct":      round(self.auto_resolved / total * 100, 2),
            "escalation_rate_pct":      round(self.escalated_exceptions / total * 100, 2),
            "average_response_time_s":  round(avg_rt, 2),
            "min_response_time_s":      round(min(self.response_times), 2) if self.response_times else 0,
            "max_response_time_s":      round(max(self.response_times), 2) if self.response_times else 0,
            "failure_type_distribution": dict(self.failure_type_counts),
            "resolution_distribution":   dict(self.resolution_counts),
        }

    def reset(self):
        self.__init__()
        logger.info("ExceptionMetrics reset.")
