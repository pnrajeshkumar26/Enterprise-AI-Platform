from dataclasses import dataclass


@dataclass(frozen=True)
class CostEstimate:
    """Estimated compute infrastructure cost for one inference request."""

    instance_type: str
    hourly_cost_usd: float
    runtime_seconds: float
    estimated_cost_usd: float


class CostEstimator:
    """
    Estimate self-hosted inference infrastructure cost.

    Formula:

        estimated_cost_usd =
            hourly_cost_usd * runtime_seconds / 3600
    """

    def __init__(
        self,
        instance_type: str,
        hourly_cost_usd: float,
    ):
        if not instance_type.strip():
            raise ValueError("instance_type must not be empty")

        if hourly_cost_usd < 0:
            raise ValueError("hourly_cost_usd must be >= 0")

        self.instance_type = instance_type.strip()
        self.hourly_cost_usd = float(hourly_cost_usd)

    def estimate(self, runtime_seconds: float) -> CostEstimate:
        if runtime_seconds < 0:
            raise ValueError("runtime_seconds must be >= 0")

        estimated_cost_usd = (
            self.hourly_cost_usd * runtime_seconds / 3600.0
        )

        return CostEstimate(
            instance_type=self.instance_type,
            hourly_cost_usd=self.hourly_cost_usd,
            runtime_seconds=float(runtime_seconds),
            estimated_cost_usd=estimated_cost_usd,
        )
