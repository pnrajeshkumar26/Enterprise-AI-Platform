import uuid

from app.gateway.context import GatewayRequestContext
from app.gateway.decision import GatewayDecision
from app.gateway.latency import latency_tracker
from app.resources.gpu_collector import gpu_resource_collector
from app.routing.model_router import model_router


class LLMGateway:
    """
    Lightweight self-hosted LLM Gateway.

    Stage 1 responsibilities:
      - normalize request context
      - invoke the existing model router
      - produce an explainable gateway decision

    Stage 4 responsibilities:
      - read historical latency state before routing
      - attach latency signals to the gateway decision

    Stage 5 responsibilities:
      - read current GPU resource state before routing
      - attach GPU/resource signals to the gateway decision

    Future stages will add:
      - cost-aware routing
      - multi-signal routing policy
      - explainable scoring based on all signals
    """

    def create_context(
        self,
        requested_model: str,
        prompt: str,
    ) -> GatewayRequestContext:
        request_id = str(uuid.uuid4())

        return GatewayRequestContext.from_request(
            request_id=request_id,
            requested_model=requested_model,
            prompt=prompt,
        )

    def decide(
        self,
        context: GatewayRequestContext,
    ) -> GatewayDecision:

        # -----------------------------------------------------------
        # Historical latency state available before routing
        # -----------------------------------------------------------
        tinyllama_avg_latency = (
            latency_tracker.average_latency("tinyllama")
        )

        phi3_avg_latency = (
            latency_tracker.average_latency("phi3")
        )

        # -----------------------------------------------------------
        # Current GPU resource state available before routing
        # -----------------------------------------------------------
        gpu_state = gpu_resource_collector.collect()

        if context.requested_model == "auto":
            routing = model_router.route(context.prompt)

            routing_reasons = tuple(
                reason.strip()
                for reason in routing.reason.split(",")
                if reason.strip()
            )

            return GatewayDecision(
                request_id=context.request_id,
                requested_model=context.requested_model,
                selected_model=routing.selected_model,
                routing_score=routing.score,
                routing_reason=routing.reason,
                routing_reasons=routing_reasons,
                tinyllama_avg_latency=tinyllama_avg_latency,
                phi3_avg_latency=phi3_avg_latency,
                gpu_name=gpu_state.gpu_name,
                gpu_utilization_percent=(
                    gpu_state.gpu_utilization_percent
                ),
                gpu_memory_utilization_percent=(
                    gpu_state.memory_utilization_percent
                ),
                gpu_memory_total_mib=gpu_state.memory_total_mib,
                gpu_memory_used_mib=gpu_state.memory_used_mib,
                gpu_memory_free_mib=gpu_state.memory_free_mib,
            )

        return GatewayDecision(
            request_id=context.request_id,
            requested_model=context.requested_model,
            selected_model=context.requested_model,
            routing_score=0,
            routing_reason="Explicit model requested",
            routing_reasons=("explicit model requested",),
            tinyllama_avg_latency=tinyllama_avg_latency,
            phi3_avg_latency=phi3_avg_latency,
            gpu_name=gpu_state.gpu_name,
            gpu_utilization_percent=(
                gpu_state.gpu_utilization_percent
            ),
            gpu_memory_utilization_percent=(
                gpu_state.memory_utilization_percent
            ),
            gpu_memory_total_mib=gpu_state.memory_total_mib,
            gpu_memory_used_mib=gpu_state.memory_used_mib,
            gpu_memory_free_mib=gpu_state.memory_free_mib,
        )


llm_gateway = LLMGateway()
