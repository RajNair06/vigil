import json
import os
import random
import requests
from dotenv import load_dotenv
from fake_app.app import random_ip, generate_log, LOGFILE

load_dotenv()
INGEST_URL = os.getenv("INGEST_URL")


def send_log_batch(logs):
    batch_string = "\n".join(json.dumps(log) for log in logs)

    response = requests.post(
        INGEST_URL,
        data=batch_string,
        headers={"Content-Type": "text/plain"}
    )

    print("Batch sent:", response.status_code)
    print(response.text)


def batch_write_log(logs):
    with open(LOGFILE, 'a') as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")


def ddos_attack(rps):
    logs = []

    for _ in range(rps):
        log = generate_log()

        if random.random() < 0.9:
            log["status_code"] = 200
        else:
            log["status_code"] = random.choice([500, 502, 503])

        logs.append(log)

    batch_write_log(logs)
    send_log_batch(logs)


def brute_force(rps):
    attacker_ip = random_ip()
    logs = []

    for _ in range(rps):
        log = generate_log()
        log['client_ip'] = attacker_ip
        log["endpoint"] = "/api/login"
        log["status_code"] = random.choice([401, 401, 401, 403])

        logs.append(log)

    batch_write_log(logs)
    send_log_batch(logs)


if __name__ == "__main__":
    brute_force(100)
    ddos_attack(300)