"""Loyalty points service. It works. It tells nobody anything.

API:
  POST /points/{customer}   body {"points": 10}   adds points (a bonus is added for big purchases); returns the new total
  GET  /points/{customer}   returns the total; 404 if the customer is unknown
  GET  /healthz             liveness: the process is alive
  GET  /readyz              readiness: the service can take traffic

Your job: make it observable WITHOUT changing what it does. Everything goes in this file.
"""
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="loyalty")
TOTALS = {}


class Purchase(BaseModel):
    points: int


def compute_bonus(points: int) -> int:
    """10% bonus on purchases of 100 points or more. Pretend it is slow: it calls a rules engine."""
    time.sleep(0.05)
    return points // 10 if points >= 100 else 0


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.post("/points/{customer}")
def add_points(customer: str, p: Purchase):
    if p.points <= 0:
        raise HTTPException(status_code=422, detail="points must be positive")
    bonus = compute_bonus(p.points)
    TOTALS[customer] = TOTALS.get(customer, 0) + p.points + bonus
    return {"customer": customer, "total": TOTALS[customer], "bonus": bonus}


@app.get("/points/{customer}")
def get_points(customer: str):
    if customer not in TOTALS:
        raise HTTPException(status_code=404, detail="unknown customer")
    return {"customer": customer, "total": TOTALS[customer]}


# TODO 1 - LOGS. One JSON object per line on stdout (use the logging module, not print):
#   ts, level, service ("loyalty"), msg, request_id, trace_id (when a trace is active, else ""), and for the access line:
#   method, route (the TEMPLATE like /points/{customer}), status, duration_ms (a number).
#   Write ONE access line per request, from a middleware. The request id comes from the incoming X-Request-ID header or a new uuid,
#   and is returned to the client in the X-Request-ID response header. Never log the Authorization header.
#   Also log a business line "points added" with the customer id (not the points total) at info level when points are added.
#
# TODO 2 - METRICS (prometheus_client), exposed at GET /metrics:
#   loyalty_http_requests_total{method,route,status}            Counter
#   loyalty_http_request_duration_seconds{method,route}         Histogram with buckets you choose (think: what is slow here?)
#   loyalty_http_requests_in_flight                             Gauge
#   loyalty_points_awarded_total                                Counter of points awarded, including the bonus
#   The route label is the route TEMPLATE (request.scope["route"].path), never the real URL. /metrics itself must not be counted.
#
# TODO 3 - TRACES (OpenTelemetry): if OTEL_EXPORTER_OTLP_ENDPOINT is set, export spans over OTLP/HTTP (service.name from OTEL_SERVICE_NAME)
#   with the FastAPI instrumentation, and add your own span named "compute_bonus" around the call to compute_bonus() with the attribute
#   points (the size of the purchase). /healthz, /readyz and /metrics must not create spans.
