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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Model",
            data.get("model", model),
        )

    with col2:
        st.metric(
            "Status",
            data.get("status", "unknown"),
        )

    with col3:
        st.metric(
            "Latency",
            f"{elapsed:.2f}s",
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
