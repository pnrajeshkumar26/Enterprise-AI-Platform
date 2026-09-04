from dataclasses import dataclass

from app.routing.token_capacity import TokenCapacityState


@dataclass(frozen=True)
class CapacityRoutingResult:
    """Result of capacity-aware model selection."""

    selected_model: str
    overridden: bool
    reason: str


class CapacityAwareRouter:
    """Apply token-capacity constraints after base model routing."""

    def select(
        self,
        requested_model: str,
        base_selected_model: str,
        tinyllama_capacity: TokenCapacityState,
        phi3_capacity: TokenCapacityState,
    ) -> CapacityRoutingResult:
        normalized_requested_model = (
            requested_model or "auto"
        ).strip().lower()

        normalized_base_model = (
            base_selected_model or ""
        ).strip().lower()

        capacities = {
            "tinyllama": tinyllama_capacity,
            "phi3": phi3_capacity,
        }

        selected_capacity = capacities.get(
            normalized_base_model
        )

        if selected_capacity is None:
            raise ValueError(
                f"Unsupported routed model: "
                f"{normalized_base_model}"
            )

        # ---------------------------------------------------------
        # Explicit model selection
        #
        # Respect the user's explicit model choice.
        # Do not silently switch models.
        # ---------------------------------------------------------
        if normalized_requested_model != "auto":
            if not selected_capacity.has_capacity:
                raise ValueError(
                    f"Model '{normalized_base_model}' cannot "
                    f"accommodate the requested input/output budget. "
                    f"Context capacity={selected_capacity.max_context_tokens}, "
                    f"estimated total tokens="
                    f"{selected_capacity.estimated_total_tokens}."
                )

            return CapacityRoutingResult(
                selected_model=normalized_base_model,
                overridden=False,
                reason="explicit model has sufficient token capacity",
            )

        # ---------------------------------------------------------
        # AUTO routing
        #
        # Keep the base routing decision when the selected model
        # has enough capacity.
        # ---------------------------------------------------------
        if selected_capacity.has_capacity:
            return CapacityRoutingResult(
                selected_model=normalized_base_model,
                overridden=False,
                reason="selected model has sufficient token capacity",
            )

        # ---------------------------------------------------------
        # Capacity fallback
        #
        # Base model cannot fit. Try the alternate model.
        # ---------------------------------------------------------
        alternate_model = (
            "phi3"
            if normalized_base_model == "tinyllama"
            else "tinyllama"
        )

        alternate_capacity = capacities[alternate_model]

        if alternate_capacity.has_capacity:
            return CapacityRoutingResult(
                selected_model=alternate_model,
                overridden=True,
                reason=(
                    "capacity override: "
                    f"{normalized_base_model} cannot accommodate "
                    "the request; "
                    f"{alternate_model} has sufficient capacity"
                ),
            )

        # ---------------------------------------------------------
        # Both models cannot safely accommodate the request.
        # ---------------------------------------------------------
        raise ValueError(
            "Request exceeds available token capacity on both "
            "configured models. Reduce input size or requested "
            "max_output_tokens."
        )


capacity_aware_router = CapacityAwareRouter()
