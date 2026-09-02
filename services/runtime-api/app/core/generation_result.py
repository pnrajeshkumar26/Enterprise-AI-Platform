from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationResult:
    """
    Normalized generation result shared by inference backends.

    Token counts are backend-provided when available or calculated
    using the model-compatible tokenizer when necessary.
    """

    text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
