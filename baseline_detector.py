import numpy as np
from sqlalchemy.orm import Session
from db.models import Feature

HISTORY_WINDOW=100
Z_THRESHOLD=2.5

def zscore_anomaly(value,series):
    mean=np.mean(series)
    std=np.std(series)
    if std==0:
        return False
    z=(value-mean)/std
    print(f"value={value} mean={mean:.2f} std={std:.2f} z={z:.2f}")
    
    return abs(z)>Z_THRESHOLD

def baseline_anomaly_detection(db:Session,feature:Feature):
    history=db.query(Feature).filter(Feature.id<feature.id).filter(Feature.is_attack==False).order_by(Feature.id.desc()).limit(HISTORY_WINDOW).all()
    if len(history)<30:
        return False
    
    request_counts=[f.request_count for f in history]
    error_ratios=[f.error_ratio for f in history]
    unique_ips=[f.unique_ips for f in history]
    response_times=[f.avg_response_time for f in history]

    anomalies=[]
    anomalies.append(zscore_anomaly(feature.request_count,request_counts))
    anomalies.append(zscore_anomaly(feature.error_ratio,error_ratios))
    anomalies.append(zscore_anomaly(feature.unique_ips,unique_ips))
    anomalies.append(zscore_anomaly(feature.avg_response_time,response_times))
    return any(anomalies)
