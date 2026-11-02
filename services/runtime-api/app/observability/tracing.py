"""OpenTelemetry tracing configuration for the Enterprise Runtime API."""

from __future__ import annotations

import math
import os
import re
from urllib.parse import urlsplit

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased


_tracer_provider: TracerProvider | None = None


def _get_traces_endpoint() -> str | None:
    """Return the configured OTLP HTTP traces endpoint, if any."""

    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")

    if traces_endpoint:
        return traces_endpoint.rstrip("/")

    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if base_endpoint:
        return f"{base_endpoint.rstrip('/')}/v1/traces"

    # Tracing will still work locally, but spans will not be exported.
    return None



def _get_sampler():
    """Build a parent-based trace-ID ratio sampler from environment settings."""

    sampler_name = os.getenv(
        "OTEL_TRACES_SAMPLER",
        "parentbased_traceidratio",
    ).strip().lower()

    if sampler_name != "parentbased_traceidratio":
        raise ValueError(
            "OTEL_TRACES_SAMPLER must be parentbased_traceidratio"
        )

    raw_ratio = os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0")

    try:
        ratio = float(raw_ratio)
    except ValueError as exc:
        raise ValueError(
            "OTEL_TRACES_SAMPLER_ARG must be a number between 0 and 1"
        ) from exc

    if not math.isfinite(ratio) or not 0.0 <= ratio <= 1.0:
        raise ValueError(
            "OTEL_TRACES_SAMPLER_ARG must be between 0 and 1"
        )

    return ParentBased(root=TraceIdRatioBased(ratio))


def _exclude_exporter_endpoint(endpoint: str) -> None:
    """Prevent tracing the HTTP requests used to export telemetry."""

    parsed = urlsplit(endpoint)

    if not parsed.scheme or not parsed.netloc:
        return

    exporter_url = (
        f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
    )

    # Exclude only the exporter endpoint, not every service on its host.
    pattern = rf"^{re.escape(exporter_url)}(?:\?.*)?$"

    env_name = "OTEL_PYTHON_REQUESTS_EXCLUDED_URLS"
    existing = os.getenv(env_name, "")

    patterns = [
        item.strip()
        for item in existing.split(",")
        if item.strip()
    ]

    if pattern not in patterns:
        patterns.append(pattern)
        os.environ[env_name] = ",".join(patterns)


def initialize_tracing() -> TracerProvider:
    """Initialize OpenTelemetry once for this application process."""

    global _tracer_provider

    if _tracer_provider is not None:
        return _tracer_provider

    service_name = (
        os.getenv("OTEL_SERVICE_NAME", "").strip()
        or "enterprise-runtime-api"
    )

    os.environ.setdefault("OTEL_SERVICE_NAME", service_name)

    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
        }
    )

    provider = TracerProvider(resource=resource, sampler=_get_sampler())
    trace.set_tracer_provider(provider)

    endpoint = _get_traces_endpoint()

    if endpoint:
        _exclude_exporter_endpoint(endpoint)

        exporter = OTLPSpanExporter(endpoint=endpoint)

        provider.add_span_processor(
            BatchSpanProcessor(exporter)
        )

    # Keep logs on stdout for the agreed Alloy -> Loki pipeline.
    # Inject trace context into Python logs without installing a
    # separate OpenTelemetry log-export handler.
    os.environ["OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION"] = "false"

    LoggingInstrumentor().instrument(
        tracer_provider=provider,
        inject_trace_context=True,
        set_logging_format=False,
    )

    # Create spans for outbound HTTP requests, including calls to vLLM.
    RequestsInstrumentor().instrument(
        tracer_provider=provider
    )

    _tracer_provider = provider

    return provider


def instrument_fastapi_app(
    app: FastAPI,
    tracer_provider: TracerProvider,
) -> None:
    """Instrument incoming API requests, excluding Prometheus scraping."""

    excluded_urls = os.getenv(
        "OTEL_PYTHON_FASTAPI_EXCLUDED_URLS",
        r"/metrics(?:/.*)?$",
    )

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls=excluded_urls,
    )