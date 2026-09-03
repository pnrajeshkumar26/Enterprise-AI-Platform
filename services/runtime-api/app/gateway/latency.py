from collections import defaultdict, deque


class LatencyTracker:
    """
    Maintain bounded rolling latency history per model.
    """

    def __init__(self, window_size: int = 20):
        if window_size <= 0:
            raise ValueError("window_size must be > 0")

        self.window_size = window_size
        self._samples = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )

    def record(
        self,
        model: str,
        latency_seconds: float,
    ) -> None:
        model = model.strip().lower()

        if not model:
            raise ValueError("model must not be empty")

        if latency_seconds < 0:
            raise ValueError("latency_seconds must be >= 0")

        self._samples[model].append(
            float(latency_seconds)
        )

    def average_latency(
        self,
        model: str,
    ) -> float | None:
        model = model.strip().lower()

        samples = self._samples.get(model)

        if not samples:
            return None

        return sum(samples) / len(samples)

    def sample_count(
        self,
        model: str,
    ) -> int:
        model = model.strip().lower()

        return len(
            self._samples.get(model, ())
        )

    def recent_samples(
        self,
        model: str,
    ) -> tuple[float, ...]:
        model = model.strip().lower()

        return tuple(
            self._samples.get(model, ())
        )


latency_tracker = LatencyTracker()
