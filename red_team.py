import json
from fake_app.app import random_ip, generate_log, LOGFILE
import random


def batch_write_log(logs):
    with open(LOGFILE, 'a') as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")


def ddos_attack(rps):
    logs = []
    for i in range(rps):
        if random.random() < 0.9:
            log=generate_log()
            log["status_code"] = 200
        else:
            log["status_code"] = random.choice([500, 502, 503])
        logs.append(log)

    batch_write_log(logs)

def brute_force(rps):
    attacker_ip=random_ip()
    logs=[]
    for i in range(rps):
        log=generate_log()
        log['client_ip']=attacker_ip
        log["endpoint"] = "/api/login"
        log["status_code"] = random.choice([401, 401, 401, 403])
        logs.append(log)
    batch_write_log(logs)



brute_force(10)
ddos_attack(10)



