"""
Vision API cost tracking and budget management.

Prevents runaway costs by tracking API calls and enforcing budget limits.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VisionAPITracker:
    """Tracks Vision API costs and enforces budget limits"""

    def __init__(
        self,
        cost_per_call: float = 0.02,
        max_budget: float = 10.0,
        warn_threshold: float = 5.0,
        max_calls_per_minute: int = 10,
        max_calls_per_run: int = 500
    ):
        """
        Initialize cost tracker.

        Args:
            cost_per_call: Estimated cost per API call (default: $0.02)
            max_budget: Maximum spending per run (default: $10.00)
            warn_threshold: Warn when spending exceeds this (default: $5.00)
            max_calls_per_minute: Rate limit (default: 10)
            max_calls_per_run: Maximum calls per run (default: 500)
        """
        self.cost_per_call = cost_per_call
        self.max_budget = max_budget
        self.warn_threshold = warn_threshold
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_run = max_calls_per_run

        self.calls = 0
        self.estimated_cost = 0.0
        self.warned = False
        self.budget_exceeded = False

        logger.info(f"Vision API cost tracker initialized: "
                   f"${cost_per_call}/call, max budget ${max_budget}")

    def can_make_call(self) -> bool:
        """
        Check if another API call can be made within budget.

        Returns:
            True if call is allowed, False if budget exceeded
        """
        # Check budget
        if self.estimated_cost >= self.max_budget:
            if not self.budget_exceeded:
                logger.error(f"🚫 Vision API budget exceeded: "
                           f"${self.estimated_cost:.2f} >= ${self.max_budget:.2f}")
                self.budget_exceeded = True
            return False

        # Check max calls
        if self.calls >= self.max_calls_per_run:
            logger.error(f"🚫 Vision API max calls exceeded: "
                        f"{self.calls} >= {self.max_calls_per_run}")
            return False

        return True

    def track_call(self, actual_cost: Optional[float] = None):
        """
        Track an API call.

        Args:
            actual_cost: Actual cost if known, otherwise use estimated cost
        """
        self.calls += 1
        cost = actual_cost if actual_cost is not None else self.cost_per_call
        self.estimated_cost += cost

        logger.debug(f"Vision API call #{self.calls}: +${cost:.2f} "
                    f"(total: ${self.estimated_cost:.2f})")

        # Warn at threshold
        if not self.warned and self.estimated_cost >= self.warn_threshold:
            logger.warning(f"⚠️  Vision API spending reached ${self.estimated_cost:.2f} "
                         f"(threshold: ${self.warn_threshold:.2f})")
            self.warned = True

    def get_statistics(self) -> dict:
        """Get cost tracking statistics"""
        return {
            'calls_made': self.calls,
            'estimated_cost': self.estimated_cost,
            'max_budget': self.max_budget,
            'budget_remaining': max(0, self.max_budget - self.estimated_cost),
            'budget_used_percent': (self.estimated_cost / self.max_budget * 100
                                   if self.max_budget > 0 else 0),
            'budget_exceeded': self.budget_exceeded
        }

    def log_summary(self):
        """Log cost tracking summary"""
        stats = self.get_statistics()
        logger.info(f"Vision API Cost Summary:")
        logger.info(f"  Calls made: {stats['calls_made']}")
        logger.info(f"  Estimated cost: ${stats['estimated_cost']:.2f}")
        logger.info(f"  Budget remaining: ${stats['budget_remaining']:.2f}")
        logger.info(f"  Budget used: {stats['budget_used_percent']:.1f}%")

        if stats['budget_exceeded']:
            logger.warning(f"  ⚠️  Budget was exceeded during processing")
