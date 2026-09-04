from dataclasses import dataclass


@dataclass(frozen=True)
class OutputBudgetPolicy:
    """Model-specific default output token budgets."""

    default_by_model: dict[str, int]

    def get_default(self, model: str) -> int:
        normalized_model = (model or "").strip().lower()

        if normalized_model not in self.default_by_model:
            raise ValueError(
                f"No output-token budget configured for model: "
                f"{normalized_model}"
            )

        return self.default_by_model[normalized_model]

    def resolve(
        self,
        model: str,
        requested_budget: int | None,
    ) -> int:
        if requested_budget is not None:
            if requested_budget < 1:
                raise ValueError(
                    "max_output_tokens must be >= 1"
                )

            return requested_budget

        return self.get_default(model)


output_budget_policy = OutputBudgetPolicy(
    default_by_model={
        "tinyllama": 512,
        "phi3": 1024,
    }
)
