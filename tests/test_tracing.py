import logging

import pytest

from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind
from opentelemetry.sdk.trace.sampling import ParentBased

from app.main import app
from app.routers import models as models_router
from app.observability.tracing import (
    _get_sampler,
    _get_traces_endpoint,
    initialize_tracing,
)


def test_explicit_traces_endpoint_takes_precedence(monkeypatch):
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://alloy:4318",
    )
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "http://alloy:4318/v1/traces/",
    )

    assert (
        _get_traces_endpoint()
        == "http://alloy:4318/v1/traces"
    )


def test_base_otlp_endpoint_adds_traces_path(monkeypatch):
    monkeypatch.delenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        raising=False,
    )
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://alloy:4318/",
    )

    assert (
        _get_traces_endpoint()
        == "http://alloy:4318/v1/traces"
    )


def test_health_request_creates_server_span():
    provider = initialize_tracing()
    exporter = InMemorySpanExporter()

    provider.add_span_processor(
        SimpleSpanProcessor(exporter)
    )

    response = TestClient(app).get("/health")

    assert response.status_code == 200

    spans = exporter.get_finished_spans()

    server_spans = [
        span
        for span in spans
        if span.kind == SpanKind.SERVER
    ]

    assert server_spans, "Expected an incoming HTTP server span"

    assert any(
        "health" in span.name.lower()
        or span.attributes.get("http.route") == "/health"
        for span in server_spans
    ), "Expected a server span for the /health route"


def test_logs_include_trace_context(caplog):
    initialize_tracing()

    logger = logging.getLogger("tests.tracing")
    tracer = trace.get_tracer("tests.tracing")

    with caplog.at_level(logging.INFO, logger=logger.name):
        with tracer.start_as_current_span("log-correlation-test"):
            logger.info("trace-correlation-probe")

    records = [
        record
        for record in caplog.records
        if record.getMessage() == "trace-correlation-probe"
    ]

    assert records, "Expected the test log record"

    record = records[-1]

    assert getattr(record, "otelTraceID", "0") != "0"
    assert getattr(record, "otelSpanID", "0") != "0"

def test_parent_based_sampler_accepts_configured_ratio(monkeypatch):
    monkeypatch.setenv("OTEL_TRACES_SAMPLER", "parentbased_traceidratio")
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", "0.25")

    assert isinstance(_get_sampler(), ParentBased)


def test_sampler_rejects_invalid_ratio(monkeypatch):
    monkeypatch.setenv("OTEL_TRACES_SAMPLER", "parentbased_traceidratio")
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", "1.5")

    with pytest.raises(ValueError):
        _get_sampler()


def test_validation_error_does_not_log_request_values(caplog):
    sensitive_value = "DO_NOT_LOG_SENSITIVE_PROMPT_7162"
    caplog.set_level(logging.INFO)

    response = TestClient(app).post(
        "/generate",
        json={
            "model": "tinyllama",
            "prompt": {"sensitive": sensitive_value},
        },
    )

    assert response.status_code == 422
    assert sensitive_value not in caplog.text
    assert "Request validation failed error_count=" in caplog.text


def test_unhandled_error_is_trace_correlated_and_sanitized(
    monkeypatch,
    caplog,
):
    sensitive_path = "PRIVATE_CUSTOMER_REFERENCE_8164"
    sensitive_error = "SECRET_BACKEND_EXCEPTION_TEXT"

    def raise_test_error(_model_name):
        raise RuntimeError(sensitive_error)

    monkeypatch.setattr(
        models_router.model_service,
        "get_model",
        raise_test_error,
    )
    caplog.set_level(logging.ERROR)

    response = TestClient(
        app,
        raise_server_exceptions=False,
    ).get(f"/models/{sensitive_path}")

    assert response.status_code == 500
    assert sensitive_path not in caplog.text
    assert sensitive_error not in caplog.text

    failure_records = [
        record for record in caplog.records
        if "http_request_failed" in record.getMessage()
    ]

    assert failure_records
    record = failure_records[-1]

    assert "route=/models/{model_name}" in record.getMessage()
    assert getattr(record, "otelTraceID", "0") != "0"
    assert getattr(record, "otelSpanID", "0") != "0"
