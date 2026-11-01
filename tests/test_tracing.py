import logging

from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

from app.main import app
from app.observability.tracing import (
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