from dataclasses import dataclass
import re


@dataclass
class RoutingDecision:
    selected_model: str
    score: int
    reason: str


class ModelRouter:
    """
    Deterministic model router for the Enterprise AI Platform.

    AUTO mode:
      low complexity  -> tinyllama
      high complexity -> phi3

    Manual model selection bypasses this router.
    """

    # Ordered collection for deterministic matching/reasons.
    COMPLEX_KEYWORDS = (
        "analyze",
        "analysis",
        "architecture",
        "architect",
        "compare",
        "comparison",
        "debug",
        "debugging",
        "design",
        "evaluate",
        "explain why",
        "investigate",
        "optimize",
        "reason",
        "reasoning",
        "trade-off",
        "tradeoffs",
        "troubleshoot",
        "troubleshooting",
    )

    CODE_KEYWORDS = (
        "code",
        "script",
        "python",
        "bash",
        "shell",
        "sql",
        "yaml",
        "kubernetes",
        "dockerfile",
        "terraform",
        "ansible",
        "javascript",
        "java",
        "docker",
        "vllm",
        "llama.cpp",
        "prometheus",
        "grafana",
        "gpu",
        "cuda",
        "inference",
        "llmops",
    )

    def route(self, prompt: str) -> RoutingDecision:
        text = prompt.strip().lower()

        if not text:
            return RoutingDecision(
                selected_model="tinyllama",
                score=0,
                reason="Empty/very short request",
            )

        score = 0
        reasons = []

        # ---------------------------------------------------------
        # Prompt length
        # ---------------------------------------------------------
        if len(text) >= 500:
            score += 2
            reasons.append("long prompt")
        elif len(text) >= 250:
            score += 1
            reasons.append("moderately long prompt")

        # ---------------------------------------------------------
        # Multiple questions / multi-step style
        # ---------------------------------------------------------
        question_count = text.count("?")

        if question_count >= 2:
            score += 1
            reasons.append("multiple questions")

        if re.search(
            r"\b(first|then|finally|step 1|step 2|step 3)\b",
            text,
        ):
            score += 1
            reasons.append("multi-step request")

        # ---------------------------------------------------------
        # Complexity indicators
        # ---------------------------------------------------------
        matched_complex = [
            keyword
            for keyword in self.COMPLEX_KEYWORDS
            if keyword in text
        ]

        if matched_complex:
            score += 2
            reasons.append(
                f"complexity keyword: {matched_complex[0]}"
            )

        # Additional complexity signal when multiple indicators exist.
        if len(matched_complex) >= 2:
            score += 1
            reasons.append("multiple complexity indicators")

        # ---------------------------------------------------------
        # Technical / code indicators
        # ---------------------------------------------------------
        matched_code = [
            keyword
            for keyword in self.CODE_KEYWORDS
            if keyword in text
        ]

        if matched_code:
            score += 2
            reasons.append(
                f"technical/code keyword: {matched_code[0]}"
            )

        # Additional signal for highly technical prompts.
        if len(matched_code) >= 2:
            score += 1
            reasons.append("multiple technical indicators")

        if "```" in text:
            score += 2
            reasons.append("code block detected")

        # ---------------------------------------------------------
        # Routing threshold
        # ---------------------------------------------------------
        if score >= 3:
            selected_model = "phi3"
        else:
            selected_model = "tinyllama"

        reason = (
            ", ".join(reasons)
            if reasons
            else "simple request"
        )

        return RoutingDecision(
            selected_model=selected_model,
            score=score,
            reason=reason,
        )


model_router = ModelRouter()
