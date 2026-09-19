import json
import os
import time
import requests
import streamlit as st


st.set_page_config(
    page_title="Enterprise AI Platform",
    page_icon="🤖",
    layout="wide",
)


RUNTIME_API_URL = os.getenv(
    "RUNTIME_API_URL",
    "http://127.0.0.1:8001",
)

EVAL_JUDGE_URL = os.getenv(
    "EVAL_JUDGE_URL",
    "http://enterprise-qwen-judge:8000/v1",
)

EVAL_JUDGE_MODEL = os.getenv(
    "EVAL_JUDGE_MODEL",
    "Qwen/Qwen2.5-1.5B-Instruct",
)


st.title("🤖 Enterprise AI Platform")

st.caption(
    "Streamlit → Runtime API → Model Router → llama.cpp / vLLM → NVIDIA GPU"
)


# -------------------------------------------------------------------
# LLM-as-a-Judge
# -------------------------------------------------------------------

def evaluate_with_llm_judge(
    prompt: str,
    response: str,
) -> dict:
    """Evaluate a generated response using the configured LLM judge."""

    judge_prompt = f"""
Evaluate the following model response.

User prompt:
{prompt}

Model response:
{response}

Score each criterion from 1 to 5:

1. correctness
2. relevance
3. completeness
4. instruction_following

Return ONLY valid JSON with this exact structure:

{{
  "correctness": 1,
  "relevance": 1,
  "completeness": 1,
  "instruction_following": 1,
  "evidence": "Brief evidence supporting the scores."
}}

Do not use Markdown code fences.
Do not include additional fields.
"""

    payload = {
        "model": EVAL_JUDGE_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an LLM evaluation judge. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": judge_prompt,
            },
        ],
        "temperature": 0,
        "max_tokens": 300,
    }

    judge_response = requests.post(
        f"{EVAL_JUDGE_URL}/chat/completions",
        json=payload,
        timeout=60,
    )

    judge_response.raise_for_status()

    response_body = judge_response.json()

    judge_text = (
        response_body["choices"][0]["message"]["content"]
    ).strip()

    if judge_text.startswith("```"):
        lines = judge_text.splitlines()

        if lines and lines[0].strip().lower() in (
            "```",
            "```json",
        ):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        judge_text = "\n".join(lines).strip()

    result = json.loads(judge_text)

    required_fields = [
        "correctness",
        "relevance",
        "completeness",
        "instruction_following",
        "evidence",
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"Judge response missing required field: {field}"
            )

    score_fields = [
        "correctness",
        "relevance",
        "completeness",
        "instruction_following",
    ]

    for field in score_fields:
        try:
            score = float(result[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Judge score '{field}' is not numeric"
            ) from exc

        if not 1 <= score <= 5:
            raise ValueError(
                f"Judge score '{field}' must be between 1 and 5"
            )

        result[field] = int(score) if score.is_integer() else score

    weights = {
        "correctness": 0.40,
        "relevance": 0.25,
        "completeness": 0.20,
        "instruction_following": 0.15,
    }

    overall_score = sum(
        float(result[field]) * weight
        for field, weight in weights.items()
    )

    result["overall_score"] = round(
        overall_score,
        2,
    )
    result["passed"] = overall_score >= 3.5
    result["judge_model"] = EVAL_JUDGE_MODEL

    usage = response_body.get("usage", {})

    result["input_tokens"] = usage.get(
        "prompt_tokens",
        0,
    )
    result["output_tokens"] = usage.get(
        "completion_tokens",
        0,
    )
    result["total_tokens"] = usage.get(
        "total_tokens",
        0,
    )

    return result


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

with st.sidebar:
    st.header("Model")

    model = st.selectbox(
        "Select model",
        [
            "auto",
            "tinyllama",
            "phi3",
        ],
        index=0,
    )

    if model == "auto":
        st.info(
            "AUTO: simple requests use TinyLlama; "
            "complex and technical requests use Phi-3."
        )
    elif model == "tinyllama":
        st.caption("Manual route → TinyLlama / llama.cpp")
    elif model == "phi3":
        st.caption("Manual route → Phi-3 / vLLM")

    st.divider()

    st.subheader("Runtime")

    try:
        health_response = requests.get(
            f"{RUNTIME_API_URL}/health",
            timeout=5,
        )

        if health_response.ok:
            health = health_response.json()

            st.success("Runtime API: Healthy")

            st.write(
                f"Engine: {health.get('inference_engine', 'N/A')}"
            )

            st.write(
                f"Models: {health.get('models_configured', 'N/A')}"
            )

            st.write(
                f"GPU: {health.get('gpu_available', 'N/A')}"
            )
        else:
            st.error("Runtime API health check failed")

    except requests.RequestException as exc:
        st.error(f"Runtime API unavailable: {exc}")


# -------------------------------------------------------------------
# Main chat area
# -------------------------------------------------------------------

st.subheader("Chat")

prompt = st.text_area(
    "Enter your prompt",
    height=180,
    placeholder="Ask something about Kubernetes, LLMs, Python, etc.",
)


generate_col, evaluate_col = st.columns(2)

with generate_col:
    generate = st.button(
        "🚀 Generate",
        type="primary",
        use_container_width=True,
    )

with evaluate_col:
    evaluate = st.button(
        "🧪 Generate & Evaluate",
        use_container_width=True,
    )


if generate or evaluate:

    if not prompt.strip():
        st.warning("Please enter a prompt.")
        st.stop()

    payload = {
        "model": model,
        "prompt": prompt,
    }

    with st.spinner("Generating response..."):

        start = time.perf_counter()

        try:
            response = requests.post(
                f"{RUNTIME_API_URL}/generate",
                json=payload,
                timeout=120,
            )

            elapsed = time.perf_counter() - start

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as exc:
            st.error(f"Runtime API request failed: {exc}")
            st.stop()

    st.success(
        f"Generation completed in {elapsed:.2f} seconds"
    )

    st.subheader("Response")

    st.write(
        data.get(
            "response",
            "No response returned.",
        )
    )


    # ------------------------------------------------------------
    # LLM-as-a-Judge Report
    # ------------------------------------------------------------

    if evaluate:
        st.divider()
        st.subheader("🧪 LLM-as-a-Judge Report")

        generated_response = data.get(
            "response",
            "No response returned.",
        )

        with st.spinner(
            "Evaluating response with LLM judge..."
        ):
            try:
                evaluation_result = (
                    evaluate_with_llm_judge(
                        prompt=prompt,
                        response=generated_response,
                    )
                )
            except Exception as exc:
                st.error(
                    "LLM judge evaluation failed: "
                    f"{exc}"
                )
                evaluation_result = None

        if evaluation_result:

            score_col1, score_col2, score_col3, score_col4 = (
                st.columns(4)
            )

            with score_col1:
                st.metric(
                    "Correctness",
                    f"{evaluation_result['correctness']}/5",
                )

            with score_col2:
                st.metric(
                    "Relevance",
                    f"{evaluation_result['relevance']}/5",
                )

            with score_col3:
                st.metric(
                    "Completeness",
                    f"{evaluation_result['completeness']}/5",
                )

            with score_col4:
                st.metric(
                    "Instruction Following",
                    (
                        f"{evaluation_result['instruction_following']}"
                        "/5"
                    ),
                )

            overall_col1, overall_col2 = st.columns(2)

            with overall_col1:
                st.metric(
                    "Overall Score",
                    f"{evaluation_result['overall_score']}/5",
                )

            with overall_col2:
                if evaluation_result["passed"]:
                    st.success("PASS — score ≥ 3.5")
                else:
                    st.error("FAIL — score < 3.5")

            st.caption(
                "Judge model: "
                f"{evaluation_result['judge_model']}"
            )

            st.markdown("### Evidence")

            evidence = evaluation_result.get(
                "evidence",
                "No evidence returned.",
            )

            if isinstance(evidence, (dict, list)):
                st.json(evidence)
            else:
                st.write(evidence)

            token_col1, token_col2, token_col3 = (
                st.columns(3)
            )

            with token_col1:
                st.metric(
                    "Judge Input Tokens",
                    evaluation_result.get(
                        "input_tokens",
                        0,
                    ),
                )

            with token_col2:
                st.metric(
                    "Judge Output Tokens",
                    evaluation_result.get(
                        "output_tokens",
                        0,
                    ),
                )

            with token_col3:
                st.metric(
                    "Judge Total Tokens",
                    evaluation_result.get(
                        "total_tokens",
                        0,
                    ),
                )


    st.divider()

    st.subheader("Request Telemetry")

    usage = data.get("usage") or {}
    performance = data.get("performance") or {}
    cost = data.get("cost") or {}
    routing = data.get("routing") or {}

    server_latency = performance.get(
        "latency_seconds",
        elapsed,
    )

    telemetry_col1, telemetry_col2, telemetry_col3, telemetry_col4 = (
        st.columns(4)
    )

    with telemetry_col1:
        st.metric(
            "Selected Model",
            data.get("model", model),
        )

    with telemetry_col2:
        st.metric(
            "Input Tokens",
            usage.get("input_tokens", "N/A"),
        )

    with telemetry_col3:
        st.metric(
            "Output Tokens",
            usage.get("output_tokens", "N/A"),
        )

    with telemetry_col4:
        st.metric(
            "Total Tokens",
            usage.get("total_tokens", "N/A"),
        )

    telemetry_col5, telemetry_col6, telemetry_col7, telemetry_col8 = (
        st.columns(4)
    )

    with telemetry_col5:
        st.metric(
            "Latency",
            f"{server_latency:.3f}s"
            if isinstance(server_latency, (int, float))
            else "N/A",
        )

    with telemetry_col6:
        estimated_cost = cost.get("estimated_usd")
        st.metric(
            "Estimated Cost",
            f"${estimated_cost:.8f}"
            if isinstance(estimated_cost, (int, float))
            else "N/A",
        )

    with telemetry_col7:
        st.metric(
            "Status",
            data.get("status", "unknown"),
        )

    with telemetry_col8:
        st.metric(
            "Routing",
            routing.get("selected_model", data.get("model", model)),
        )

    st.subheader("Routing Explanation")

    routing_reason = routing.get("reason")
    if routing_reason:
        st.info(routing_reason)

    scores = routing.get("scores") or {}
    breakdown = routing.get("breakdown") or {}

    if scores:
        score_col1, score_col2 = st.columns(2)

        with score_col1:
            st.metric(
                "TinyLlama Score",
                scores.get("tinyllama", "N/A"),
            )

        with score_col2:
            st.metric(
                "Phi-3 Score",
                scores.get("phi3", "N/A"),
            )

    if breakdown:
        with st.expander("Routing Score Breakdown"):
            for model_name in ("tinyllama", "phi3"):
                model_breakdown = breakdown.get(model_name)

                if not model_breakdown:
                    continue

                st.markdown(f"**{model_name}**")

                breakdown_col1, breakdown_col2, breakdown_col3, breakdown_col4, breakdown_col5 = (
                    st.columns(5)
                )

                with breakdown_col1:
                    st.metric(
                        "Base",
                        model_breakdown.get(
                            "base_preference",
                            "N/A",
                        ),
                    )

                with breakdown_col2:
                    st.metric(
                        "Capacity",
                        model_breakdown.get(
                            "capacity",
                            "N/A",
                        ),
                    )

                with breakdown_col3:
                    st.metric(
                        "Latency",
                        model_breakdown.get(
                            "latency",
                            "N/A",
                        ),
                    )

                with breakdown_col4:
                    st.metric(
                        "GPU Pressure",
                        model_breakdown.get(
                            "gpu_pressure",
                            "N/A",
                        ),
                    )

                with breakdown_col5:
                    st.metric(
                        "Total",
                        model_breakdown.get(
                            "total",
                            "N/A",
                        ),
            )


# -------------------------------------------------------------------
# Architecture information
# -------------------------------------------------------------------

with st.expander("Architecture"):

    st.code(
        """
Browser
   |
   v
Streamlit
   |
   | HTTP
   v
Runtime API :8000
   |
   +---- tinyllama ----> llama.cpp ----> Tesla T4
   |
   +---- phi3 ---------> vLLM ---------> Tesla T4
        """,
        language="text",
    )
