LOGFILE = '/logs/app.log'

import os
import json
import random
import time
import uuid
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGFILE = os.path.join(parent_dir, "app.log")

services = [
    "auth-service",
    "user-service",
    "payment-service",
    "order-service",
    "inventory-service",
    "gateway"
]

endpoints = [
    "/api/login",
    "/api/logout",
    "/api/user",
    "/api/user/profile",
    "/api/order",
    "/api/order/create",
    "/api/order/cancel",
    "/api/products",
    "/api/payment/process",
    "/health",
]

methods = ["GET", "POST", "PUT", "DELETE"]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "curl/7.68.0",
    "python-requests/2.31.0",
    "PostmanRuntime/7.29.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
]

status_codes = [200, 200, 200, 201, 204, 400, 401, 403, 404, 429, 500, 502, 503]


def random_ip():
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def internal_ip():
    return f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"


def generate_log():
    now = datetime.now().isoformat() + "Z"

    status = random.choice(status_codes)
    response_time = random.randint(5, 3000)

    log = {
        "timestamp": now,
        "service": random.choice(services),
        "host": internal_ip(),
         "request_id": str(uuid.uuid4()),
        "trace_id": str(uuid.uuid4()),
        "client_ip": random_ip(),
        "method": random.choice(methods),
        "endpoint": random.choice(endpoints),
        "protocol": "HTTP/1.1",
        "user_id": random.choice(
            [None, random.randint(1000, 9999)]
        ),
        "session_id": random.choice(
            [None, f"sess-{random.randint(100000,999999)}"]
        ),
        "user_agent": random.choice(user_agents),
        "status_code": status,
        "response_time_ms": response_time,
        "bytes_in": random.randint(200, 5000),
        "bytes_out": random.randint(500, 20000),
    }

    return log


def run_normal_traffic():
    while True:
        log = generate_log()

        with open(LOGFILE, "a") as f:
            f.write(json.dumps(log) + "\n")

        time.sleep(random.uniform(0.2, 2.0))


if __name__ == "__main__":
    run_normal_traffic()