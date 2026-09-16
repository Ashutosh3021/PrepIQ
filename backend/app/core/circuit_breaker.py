"""Circuit breaker for PyroCore outbound calls.

Prevents retry storms by tracking consecutive failures and blocking
further calls once a threshold is hit. After a cooldown period the
circuit transitions to half-open and allows a single test request.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3"))
_COOLDOWN_SECONDS = int(os.getenv("CIRCUIT_BREAKER_COOLDOWN_SECONDS", "300"))


class CircuitState(Enum):
    CLOSED = "closed"       # normal — calls allowed
    OPEN = "open"           # tripped — calls blocked
    HALF_OPEN = "half_open" # test — one call allowed


class CircuitBreaker:
    """Thread-safe circuit breaker for external service calls.

    Usage::

        breaker = CircuitBreaker("pyrocore")

        if breaker.is_open:
            raise RuntimeError("Service unavailable")

        try:
            result = call_service()
            breaker.record_success()
            return result
        except RateLimited:
            breaker.record_failure()
            raise
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = _FAILURE_THRESHOLD,
        cooldown_seconds: int = _COOLDOWN_SECONDS,
    ) -> None:
        self.name = name
        self._threshold = failure_threshold
        self._cooldown = timedelta(seconds=cooldown_seconds)

        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float = 0.0
        self._lock = threading.Lock()

    # ── state queries ─────────────────────────────────────────────────

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._opened_at >= self._cooldown.total_seconds():
                    self._state = CircuitState.HALF_OPEN
            return self._state

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def failures(self) -> int:
        with self._lock:
            return self._failures

    # ── state transitions ─────────────────────────────────────────────

    def record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    "[circuit:%s] half-open test succeeded → CLOSED",
                    self.name,
                )
            self._failures = 0
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self._threshold and self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "[circuit:%s] %d consecutive failures — OPEN (cooldown %ds)",
                    self.name,
                    self._failures,
                    int(self._cooldown.total_seconds()),
                )

    def reset(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = CircuitState.CLOSED
            self._opened_at = 0.0


# Module-level singleton for PyroCore calls
pyrocore_breaker = CircuitBreaker(
    name="pyrocore",
    failure_threshold=_FAILURE_THRESHOLD,
    cooldown_seconds=_COOLDOWN_SECONDS,
)
