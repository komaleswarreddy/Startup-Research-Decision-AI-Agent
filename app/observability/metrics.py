from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class Timer:
    start_time: float = field(default_factory=perf_counter)

    def elapsed_ms(self) -> float:
        return round((perf_counter() - self.start_time) * 1000, 2)
