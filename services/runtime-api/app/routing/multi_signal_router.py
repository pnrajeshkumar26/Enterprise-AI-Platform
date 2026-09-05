from dataclasses import dataclass

from app.routing.token_capacity import TokenCapacityState


@dataclass(frozen=True)
class ModelSignalSet:
    """Signals used to score one model."""

    model: str
    capacity: TokenCapacityState
    average_latency: float | None


@dataclass(frozen=True)
class ModelScoreBreakdown:
    """Explainable score contribution breakdown for one model."""

    model: str
    base_preference_score: float
    capacity_score: float
    latency_score: float
    gpu_pressure_score: float
    total_score: float


@dataclass(frozen=True)
class MultiSignalDecision:
    """Final result of multi-signal scoring with explanation."""

    selected_model: str
    tinyllama_score: float
    phi3_score: float
    tinyllama_breakdown: ModelScoreBreakdown
    phi3_breakdown: ModelScoreBreakdown
    reason: str


class MultiSignalRouter:
    """Deterministic router using multiple observable runtime signals."""

    BASE_MODEL_PREFERENCE_SCORE = 2.0

    CAPACITY_SCORES = {
        "NORMAL": 8.0,
        "WARNING": 4.0,
        "HIGH": 1.0,
    }

    def score_model(
        self,
        model: ModelSignalSet,
        base_selected_model: str,
        peer: ModelSignalSet,
        gpu_utilization_percent: float,
        gpu_memory_utilization_percent: float,
        gpu_memory_free_mib: float,
    ) -> ModelScoreBreakdown:
        if not model.capacity.has_capacity:
            return ModelScoreBreakdown(
                model=model.model,
                base_preference_score=0.0,
                capacity_score=float("-inf"),
                latency_score=0.0,
                gpu_pressure_score=0.0,
                total_score=float("-inf"),
            )

        base_preference_score = 0.0
        if model.model == base_selected_model:
            base_preference_score = self.BASE_MODEL_PREFERENCE_SCORE

        capacity_score = self.CAPACITY_SCORES.get(
            model.capacity.status,
            0.0,
        )

        latency_score = 0.0
        if (
            model.average_latency is not None
            and peer.average_latency is not None
        ):
            if model.average_latency < peer.average_latency:
                latency_score = 3.0
            elif model.average_latency > peer.average_latency:
                latency_score = -1.0

        gpu_pressure = (
            gpu_utilization_percent >= 80
            or gpu_memory_utilization_percent >= 80
            or gpu_memory_free_mib < 2048
        )

        gpu_pressure_score = 0.0
        if gpu_pressure:
            if model.model == "tinyllama":
                gpu_pressure_score = 1.0
            elif model.model == "phi3":
                gpu_pressure_score = -1.0

        total_score = (
            base_preference_score
            + capacity_score
            + latency_score
            + gpu_pressure_score
        )

        return ModelScoreBreakdown(
            model=model.model,
            base_preference_score=base_preference_score,
            capacity_score=capacity_score,
            latency_score=latency_score,
            gpu_pressure_score=gpu_pressure_score,
            total_score=total_score,
        )

    def decide(
        self,
        base_selected_model: str,
        tinyllama_capacity: TokenCapacityState,
        phi3_capacity: TokenCapacityState,
        tinyllama_avg_latency: float | None,
        phi3_avg_latency: float | None,
        gpu_utilization_percent: float,
        gpu_memory_utilization_percent: float,
        gpu_memory_free_mib: float,
    ) -> MultiSignalDecision:
        tinyllama = ModelSignalSet(
            model="tinyllama",
            capacity=tinyllama_capacity,
            average_latency=tinyllama_avg_latency,
        )

        phi3 = ModelSignalSet(
            model="phi3",
            capacity=phi3_capacity,
            average_latency=phi3_avg_latency,
        )

        tinyllama_breakdown = self.score_model(
            model=tinyllama,
            base_selected_model=base_selected_model,
            peer=phi3,
            gpu_utilization_percent=gpu_utilization_percent,
            gpu_memory_utilization_percent=gpu_memory_utilization_percent,
            gpu_memory_free_mib=gpu_memory_free_mib,
        )

        phi3_breakdown = self.score_model(
            model=phi3,
            base_selected_model=base_selected_model,
            peer=tinyllama,
            gpu_utilization_percent=gpu_utilization_percent,
            gpu_memory_utilization_percent=gpu_memory_utilization_percent,
            gpu_memory_free_mib=gpu_memory_free_mib,
        )

        tinyllama_score = tinyllama_breakdown.total_score
        phi3_score = phi3_breakdown.total_score

        if tinyllama_score == float("-inf") and phi3_score == float("-inf"):
            raise ValueError(
                "No configured model can accommodate the request."
            )

        if phi3_score > tinyllama_score:
            selected_model = "phi3"
        elif tinyllama_score > phi3_score:
            selected_model = "tinyllama"
        else:
            # Preserve the existing/base routing decision when signals tie.
            selected_model = base_selected_model

        reason = (
            f"multi-signal scores: "
            f"tinyllama={tinyllama_score:.1f}, "
            f"phi3={phi3_score:.1f}; "
            f"selected={selected_model}"
        )

        return MultiSignalDecision(
            selected_model=selected_model,
            tinyllama_score=tinyllama_score,
            phi3_score=phi3_score,
            tinyllama_breakdown=tinyllama_breakdown,
            phi3_breakdown=phi3_breakdown,
            reason=reason,
        )


multi_signal_router = MultiSignalRouter()
