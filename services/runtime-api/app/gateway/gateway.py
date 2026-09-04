import uuid

from app.gateway.context import GatewayRequestContext
from app.gateway.decision import GatewayDecision
from app.gateway.latency import latency_tracker
from app.resources.gpu_collector import gpu_resource_collector
from app.routing.model_router import model_router
from app.routing.capacity_router import capacity_aware_router
from app.routing.multi_signal_router import multi_signal_router
from app.routing.output_budget import output_budget_policy
from app.routing.token_capacity import token_capacity_evaluator


class LLMGateway:
    """
    Lightweight self-hosted LLM Gateway.

    Responsibilities:
      - normalize request context
      - resolve output-token budget
      - invoke the existing model router
      - produce an explainable gateway decision
      - expose historical latency
      - expose current GPU/resource state
    """

    def create_context(
        self,
        requested_model: str,
        prompt: str,
        requested_output_tokens: int | None = None,
    ) -> GatewayRequestContext:
        request_id = str(uuid.uuid4())

        return GatewayRequestContext.from_request(
            request_id=request_id,
            requested_model=requested_model,
            prompt=prompt,
            requested_output_tokens=requested_output_tokens,
        )

    def decide(
        self,
        context: GatewayRequestContext,
    ) -> GatewayDecision:
        tinyllama_avg_latency = (
            latency_tracker.average_latency("tinyllama")
        )

        phi3_avg_latency = (
            latency_tracker.average_latency("phi3")
        )

        gpu_state = gpu_resource_collector.collect()

        # -----------------------------------------------------------
        # Token capacity state for both available models
        # -----------------------------------------------------------
        tinyllama_output_budget = output_budget_policy.resolve(
            "tinyllama",
            context.requested_output_tokens,
        )

        phi3_output_budget = output_budget_policy.resolve(
            "phi3",
            context.requested_output_tokens,
        )

        tinyllama_token_capacity = (
            token_capacity_evaluator.evaluate(
                model="tinyllama",
                prompt=context.prompt,
                output_token_budget=tinyllama_output_budget,
            )
        )

        phi3_token_capacity = (
            token_capacity_evaluator.evaluate(
                model="phi3",
                prompt=context.prompt,
                output_token_budget=phi3_output_budget,
            )
        )

        if context.requested_model == "auto":
            routing = model_router.route(context.prompt)

            capacity_routing = capacity_aware_router.select(
                requested_model=context.requested_model,
                base_selected_model=routing.selected_model,
                tinyllama_capacity=tinyllama_token_capacity,
                phi3_capacity=phi3_token_capacity,
            )

            # -------------------------------------------------------
            # Multi-signal optimization
            #
            # Capacity is a hard constraint. The multi-signal router
            # optimizes only across models that are actually viable.
            # -------------------------------------------------------
            multi_signal = multi_signal_router.decide(
                base_selected_model=(
                    capacity_routing.selected_model
                ),
                tinyllama_capacity=tinyllama_token_capacity,
                phi3_capacity=phi3_token_capacity,
                tinyllama_avg_latency=tinyllama_avg_latency,
                phi3_avg_latency=phi3_avg_latency,
                gpu_utilization_percent=(
                    gpu_state.gpu_utilization_percent
                ),
                gpu_memory_utilization_percent=(
                    gpu_state.memory_utilization_percent
                ),
                gpu_memory_free_mib=(
                    gpu_state.memory_free_mib
                ),
            )

            selected_model = multi_signal.selected_model

            output_budget = output_budget_policy.resolve(
                selected_model,
                context.requested_output_tokens,
            )

            routing_reasons = tuple(
                reason.strip()
                for reason in routing.reason.split(",")
                if reason.strip()
            )

            routing_reasons = (
                *routing_reasons,
                capacity_routing.reason,
                multi_signal.reason,
            )

            routing_reason = (
                f"{routing.reason}, "
                f"{capacity_routing.reason}, "
                f"{multi_signal.reason}"
            )

            return GatewayDecision(
                request_id=context.request_id,
                requested_model=context.requested_model,
                selected_model=selected_model,
                routing_score=routing.score,
                routing_reason=routing_reason,
                routing_reasons=routing_reasons,
                output_token_budget=output_budget,
                tinyllama_token_capacity=tinyllama_token_capacity,
                phi3_token_capacity=phi3_token_capacity,
                tinyllama_multi_signal_score=(
                    multi_signal.tinyllama_score
                ),
                phi3_multi_signal_score=(
                    multi_signal.phi3_score
                ),
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

        capacity_aware_router.select(
            requested_model=context.requested_model,
            base_selected_model=context.requested_model,
            tinyllama_capacity=tinyllama_token_capacity,
            phi3_capacity=phi3_token_capacity,
        )

        output_budget = output_budget_policy.resolve(
            context.requested_model,
            context.requested_output_tokens,
        )

        return GatewayDecision(
            request_id=context.request_id,
            requested_model=context.requested_model,
            selected_model=context.requested_model,
            routing_score=0,
            routing_reason="Explicit model requested",
            routing_reasons=("explicit model requested",),
            output_token_budget=output_budget,
            tinyllama_token_capacity=tinyllama_token_capacity,
            phi3_token_capacity=phi3_token_capacity,
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
