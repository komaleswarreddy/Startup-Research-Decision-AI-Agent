from dataclasses import dataclass
from time import monotonic


@dataclass
class CircuitBreaker:
    failure_threshold: int
    reset_timeout_seconds: int
    consecutive_failures: int = 0
    opened_until: float = 0.0

    def allow_request(self) -> bool:
        if self.opened_until <= 0:
            return True
        return monotonic() >= self.opened_until

    def on_success(self) -> None:
        self.consecutive_failures = 0
        self.opened_until = 0.0

    def on_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.opened_until = monotonic() + self.reset_timeout_seconds
