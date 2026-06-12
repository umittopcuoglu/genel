"""
Observability: structured logging, Prometheus metrics, OpenTelemetry tracing.
Call setup_observability(app) from main.py to wire everything in.
"""
import time
import logging
import json
import sys
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse


# ---------------------------------------------------------------------------
# 1. Structured JSON Logging
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


# ---------------------------------------------------------------------------
# 2. Prometheus Metrics
# ---------------------------------------------------------------------------

class _Metrics:
    """Lightweight in-process metrics store (no external dependency)."""

    def __init__(self) -> None:
        self.request_count: dict[str, int] = {}
        self.latency_sum: dict[str, float] = {}
        self.latency_count: dict[str, int] = {}
        # histogram buckets in seconds
        self.buckets = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        self.bucket_counts: dict[str, list[int]] = {}

    def observe(self, method: str, path: str, status: int, duration: float) -> None:
        key = f'{method}|{path}|{status}'
        self.request_count[key] = self.request_count.get(key, 0) + 1
        self.latency_sum[key] = self.latency_sum.get(key, 0.0) + duration
        self.latency_count[key] = self.latency_count.get(key, 0) + 1
        if key not in self.bucket_counts:
            self.bucket_counts[key] = [0] * len(self.buckets)
        for i, b in enumerate(self.buckets):
            if duration <= b:
                self.bucket_counts[key][i] += 1

    def render(self) -> str:
        lines: list[str] = [
            "# HELP http_requests_total Total HTTP requests",
            "# TYPE http_requests_total counter",
        ]
        for key, count in sorted(self.request_count.items()):
            method, path, status = key.split("|")
            labels = f'method="{method}",path="{path}",status="{status}"'
            lines.append(f"http_requests_total{{{labels}}} {count}")

        lines.extend([
            "# HELP http_request_duration_seconds HTTP request latency",
            "# TYPE http_request_duration_seconds histogram",
        ])
        for key in sorted(self.latency_sum.keys()):
            method, path, status = key.split("|")
            labels = f'method="{method}",path="{path}",status="{status}"'
            for i, b in enumerate(self.buckets):
                lines.append(
                    f'http_request_duration_seconds_bucket{{le="{b}",{labels}}} '
                    f"{self.bucket_counts[key][i]}"
                )
            lines.append(
                f'http_request_duration_seconds_bucket{{le="+Inf",{labels}}} '
                f"{self.latency_count[key]}"
            )
            lines.append(f"http_request_duration_seconds_sum{{{labels}}} {self.latency_sum[key]:.6f}")
            lines.append(f"http_request_duration_seconds_count{{{labels}}} {self.latency_count[key]}")

        return "\n".join(lines) + "\n"


_metrics = _Metrics()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        # Normalize path: collapse UUIDs and numeric IDs to reduce cardinality
        path = request.url.path
        _metrics.observe(request.method, path, response.status_code, duration)
        return response


# ---------------------------------------------------------------------------
# 3. OpenTelemetry Tracing (optional — graceful no-op if packages missing)
# ---------------------------------------------------------------------------

_tracer = None

def get_tracer():
    global _tracer
    if _tracer is not None:
        return _tracer
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("hotelops")
    except ImportError:
        class _NoopTracer:
            def start_as_current_span(self, name, **kw):
                import contextlib
                return contextlib.nullcontext()
        _tracer = _NoopTracer()
    return _tracer


# ---------------------------------------------------------------------------
# 4. Wire everything into the FastAPI app
# ---------------------------------------------------------------------------

def setup_observability(app: FastAPI) -> None:
    """Call once from main.py to attach metrics middleware and /metrics endpoint."""
    configure_logging()
    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        return PlainTextResponse(_metrics.render(), media_type="text/plain; version=0.0.4")

    # Initialize tracer eagerly so it's ready for first request
    get_tracer()
