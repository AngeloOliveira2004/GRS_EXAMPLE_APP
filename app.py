import os
import random
import time
from typing import Final

from flask import Flask, Response, jsonify, request
from dotenv import dotenv_values
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


def _load_env_files() -> None:
    initial_keys = set(os.environ.keys())

    for key, value in dotenv_values(".env").items():
        if value is None or key in initial_keys:
            continue

        os.environ[key] = value


_load_env_files()

APP_COLOR: Final[str] = os.getenv("APP_COLOR", "blue")
APP_VERSION: Final[str] = os.getenv("APP_VERSION", "v1")
_error_rate_env = float(os.getenv("SIMULATED_ERROR_RATE", "0.0"))
SIMULATED_ERROR_RATE: Final[float] = _error_rate_env / 100.0 if _error_rate_env > 1.0 else _error_rate_env
SIMULATED_LATENCY_MS: Final[int] = int(os.getenv("SIMULATED_LATENCY_MS", "25"))

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests",
    "Total HTTP requests handled by the application.",
    ["service", "version", "method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["service", "version", "method", "endpoint", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)


@app.before_request
def start_timer() -> None:
    request._started_at = time.perf_counter()


@app.after_request
def record_metrics(response: Response) -> Response:
    if request.path != "/metrics":
        elapsed = time.perf_counter() - getattr(request, "_started_at", time.perf_counter())
        endpoint = request.path or "unknown"
        status = str(response.status_code)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=status,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint,
            status=status,
        ).observe(elapsed)

    return response


@app.get("/")
def index():
    time.sleep(SIMULATED_LATENCY_MS / 1000)

    if SIMULATED_ERROR_RATE > 0 and random.random() < SIMULATED_ERROR_RATE:
        return jsonify(
            status="error",
            message="simulated Application failure",
        ), 500

    return jsonify(
        status="ok",
        message="Application is serving stable production traffic.",
    )


@app.get("/health")
def health():
    return jsonify(
        status="healthy",
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
