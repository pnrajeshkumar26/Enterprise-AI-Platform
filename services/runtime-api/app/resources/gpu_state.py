from dataclasses import dataclass


@dataclass(frozen=True)
class GPUResourceState:
    """
    Normalized GPU resource state consumed by the LLM Gateway.
    """

    gpu_name: str
    gpu_utilization_percent: float
    memory_utilization_percent: float
    memory_total_mib: float
    memory_used_mib: float
    memory_free_mib: float
    temperature_celsius: float | None = None
