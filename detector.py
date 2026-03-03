from sqlalchemy.orm import Session
from db.models import Feature,Detection
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime,timezone
load_dotenv()
DETECTION_LOGFILE=os.getenv("DETECTION_LOGFILE_PATH")
os.makedirs(os.path.dirname(Path(DETECTION_LOGFILE)),exist_ok=True)

def write_detection_log(feature: Feature, attack_type: str, severity: str):

    log_entry = {
        "detected_at": datetime.now(timezone.utc).isoformat(),

        "attack_type": attack_type,
        "severity": severity,

        "window_start": feature.window_start.isoformat(),
        "window_end": feature.window_end.isoformat(),

        "request_count": feature.request_count,
        "error_count": feature.error_count,
        "error_ratio": feature.error_ratio,

        "unique_ips": feature.unique_ips,
        "unique_endpoints": feature.unique_endpoints,
        "unique_user_agents": feature.unique_user_agents,

        "avg_response_time_ms": feature.avg_response_time,
    }
    print("Writing detection to file")
    print("PID:", os.getpid())

    with open(DETECTION_LOGFILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def classify_attack(feature:Feature):
    if(feature.request_count>500 and feature.unique_ips>200 and feature.error_ratio<0.2):
        return "DDOS","HIGH"
    if(feature.error_ratio>0.6 and feature.unique_ips<20 and feature.unique_endpoints<5):
        return "BRUTE_FORCE","HIGH"
    if (feature.unique_endpoints>50 and feature.unique_ips>50):
        return "VULNERABILITY_SCAN","MEDIUM"
    if (feature.avg_response_time>2000 and feature.request_count>200):
        return "RESOURCE_EXHAUSTION","MEDIUM"
    return None,None

def run_detection(db: Session):
    print("run_detection() called")

    feature = db.query(Feature).order_by(Feature.id.desc()).first()

    if not feature:
        print("No feature found")
        return

    print("Latest feature:")
    print("  id:", feature.id)
    print("  request_count:", feature.request_count)
    print("  error_ratio:", feature.error_ratio)
    print("  unique_ips:", feature.unique_ips)
    print("  unique_endpoints:", feature.unique_endpoints)
    print("  avg_response_time:", feature.avg_response_time)

    attack_type, severity = classify_attack(feature=feature)

    print("Classification result:", attack_type, severity)

    if not attack_type:
        print("No attack detected")
        return

    detection = Detection(
        window_start=feature.window_start,
        window_end=feature.window_end,
        attack_type=attack_type,
        severity=severity,
        request_count=feature.request_count
    )

    db.add(detection)
    db.commit()

    print("Detection inserted into DB")

    write_detection_log(feature, attack_type, severity)
