import uuid

from app.gateway.context import GatewayRequestContext
from app.gateway.decision import GatewayDecision
from app.routing.model_router import model_router


class LLMGateway:
    """
    Lightweight self-hosted LLM Gateway.

    Stage 1 responsibilities:
      - normalize request context
      - invoke the existing model router
      - produce an explainable gateway decision

    Future stages will add:
      - token telemetry
      - cost estimation
      - latency signals
      - GPU/resource pressure
      - multi-signal routing policy
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

        if context.requested_model == "auto":
            routing = model_router.route(context.prompt)

            return GatewayDecision(
                request_id=context.request_id,
                requested_model=context.requested_model,
                selected_model=routing.selected_model,
                routing_score=routing.score,
                routing_reason=routing.reason,
                routing_reasons=tuple(
                    reason.strip()
                    for reason in routing.reason.split(",")
                    if reason.strip()
                ),
            )

        return GatewayDecision(
            request_id=context.request_id,
            requested_model=context.requested_model,
            selected_model=context.requested_model,
            routing_score=0,
            routing_reason="Explicit model requested",
            routing_reasons=("explicit model requested",),
        )


llm_gateway = LLMGateway()
