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


st.title("🤖 Enterprise AI Platform")

st.caption(
    "Streamlit → Runtime API → Model Router → llama.cpp / vLLM → NVIDIA GPU"
)


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


generate = st.button(
    "🚀 Generate",
    type="primary",
    use_container_width=True,
)


if generate:

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
