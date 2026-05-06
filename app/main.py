import os
import time
import random
import threading
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest

app = Flask(__name__)
START_TIME = time.time()

MODE = os.environ.get("MODE", "stable")
VERSION = os.environ.get("APP_VERSION", "1.0.0")
PORT = int(os.environ.get("APP_PORT", 3000))

_chaos = {"mode": None, "duration": 0, "rate": 0.0}
_chaos_lock = threading.Lock()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "path", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency"
)

APP_UPTIME = Gauge("app_uptime_seconds", "Application uptime")
APP_MODE = Gauge("app_mode", "0 stable, 1 canary")
CHAOS_ACTIVE = Gauge("chaos_active", "0 none, 1 slow, 2 error")


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.before_request
def apply_chaos():
    if MODE != "canary":
        return

    with _chaos_lock:
        cm = _chaos["mode"]
        duration = _chaos["duration"]
        rate = _chaos["rate"]

    if cm == "slow":
        time.sleep(duration)
    elif cm == "error":
        if random.random() < rate:
            resp = jsonify({"error": "chaos error injected", "mode": "error"})
            resp.status_code = 500
            resp.headers["X-Mode"] = "canary"
            return resp


@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(
        request.method,
        request.path,
        response.status_code
    ).inc()

    REQUEST_LATENCY.observe(time.time() - getattr(request, "start_time", time.time()))

    if MODE == "canary":
        response.headers["X-Mode"] = "canary"

    return response


@app.route("/")
def index():
    return jsonify({
        "message": f"Welcome to SwiftDeploy! Running in {MODE} mode.",
        "mode": MODE,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/healthz")
def healthz():
    return jsonify({
        "status": "ok",
        "mode": MODE,
        "uptime_seconds": round(time.time() - START_TIME, 2),
    })


@app.route("/chaos", methods=["POST"])
def chaos():
    if MODE != "canary":
        return jsonify({"error": "Chaos endpoint only available in canary mode"}), 403

    data = request.get_json(force=True, silent=True) or {}
    cm = data.get("mode")

    with _chaos_lock:
        if cm == "slow":
            _chaos["mode"] = "slow"
            _chaos["duration"] = float(data.get("duration", 1))
            _chaos["rate"] = 0.0
        elif cm == "error":
            _chaos["mode"] = "error"
            _chaos["rate"] = float(data.get("rate", 0.5))
            _chaos["duration"] = 0
        elif cm == "recover":
            _chaos["mode"] = None
            _chaos["duration"] = 0
            _chaos["rate"] = 0.0
        else:
            return jsonify({"error": "Unknown chaos mode"}), 400

        snapshot = dict(_chaos)

    return jsonify({"status": "chaos applied", "chaos": snapshot})


@app.route("/metrics")
def metrics():
    APP_UPTIME.set(time.time() - START_TIME)
    APP_MODE.set(1 if MODE == "canary" else 0)

    with _chaos_lock:
        cm = _chaos["mode"]

    if cm == "slow":
        CHAOS_ACTIVE.set(1)
    elif cm == "error":
        CHAOS_ACTIVE.set(2)
    else:
        CHAOS_ACTIVE.set(0)

    return Response(generate_latest(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
