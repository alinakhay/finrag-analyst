from collections import deque
from threading import Lock


class Metrics:
    def __init__(self) -> None:
        self.requests = 0
        self.errors = 0
        self.latencies: deque[float] = deque(maxlen=500)
        self._lock = Lock()

    def observe(self, duration_ms: float, error: bool = False) -> None:
        with self._lock:
            self.requests += 1
            self.errors += int(error)
            self.latencies.append(duration_ms)

    def as_prometheus(self) -> str:
        with self._lock:
            latencies = sorted(self.latencies)
            p95_index = max(
                0,
                min(
                    len(latencies) - 1,
                    int(len(latencies) * 0.95) - 1,
                ),
            )
            p95 = latencies[p95_index] if latencies else 0
            return "\n".join(
                [
                    "# HELP catalystlens_requests_total Total research requests.",
                    "# TYPE catalystlens_requests_total counter",
                    f"catalystlens_requests_total {self.requests}",
                    "# HELP catalystlens_errors_total Total failed research requests.",
                    "# TYPE catalystlens_errors_total counter",
                    f"catalystlens_errors_total {self.errors}",
                    "# HELP catalystlens_latency_p95_ms Rolling p95 research latency.",
                    "# TYPE catalystlens_latency_p95_ms gauge",
                    f"catalystlens_latency_p95_ms {p95:.2f}",
                    "",
                ]
            )
