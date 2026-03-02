from datetime import timedelta
from sqlalchemy.orm import Session
from db.models import Log, Feature

window_size = timedelta(seconds=10)
def fetch_logs(db: Session, window_start, window_end):
    logs = (db.query(Log).filter(Log.timestamp >= window_start).filter(Log.timestamp < window_end).all())
    return logs



def calculate_features(logs, window_start, window_end):
    if not logs:
        return None
    request_count = len(logs)
    error_count = sum(1 for log in logs if log.status_code >= 400)
    error_ratio = error_count / request_count
    unique_ips = len(set(log.client_ip for log in logs))
    avg_response_time = sum(log.response_time_ms for log in logs) / request_count
    unique_endpoints = len(set(log.endpoint for log in logs))
    unique_user_agents = len(set(log.user_agent for log in logs))
    return {"window_start": window_start,"window_end": window_end,"request_count": request_count,"error_count": error_count,"error_ratio": error_ratio,"unique_ips": unique_ips,"avg_response_time": avg_response_time,"unique_endpoints": unique_endpoints,"unique_user_agents": unique_user_agents}



def store_features(db: Session, feature_data):
    feature = Feature( window_start=feature_data["window_start"],window_end=feature_data["window_end"],request_count=feature_data["request_count"],error_count=feature_data["error_count"],error_ratio=feature_data["error_ratio"],unique_ips=feature_data["unique_ips"],avg_response_time=feature_data["avg_response_time"],unique_endpoints=feature_data["unique_endpoints"],unique_user_agents=feature_data["unique_user_agents"])

    db.add(feature)