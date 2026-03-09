import os
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus"
from fastapi import FastAPI,Request,Depends,Query,Response
from prometheus_client import generate_latest,CONTENT_TYPE_LATEST,CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector
from metrics import logs_ingested_total
from typing import Optional
from contextlib import asynccontextmanager

from collections import defaultdict
import time
import threading
from detector import run_detection
from pathlib import Path
import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.database import get_db,SessionLocal
from db.models import Log,Detection
from datetime import datetime,timezone,timedelta
from aggregation_utils import fetch_logs,calculate_features,store_features,window_size
load_dotenv()
ingested_log_path=os.getenv('INGESTED_LOGFILE_PATH')
os.makedirs(os.path.dirname(Path(ingested_log_path)),exist_ok=True)


app=FastAPI()

def write_log(log):
    with open(ingested_log_path,'a') as f:
        f.write(json.dumps(log) + "\n")

@app.post('/ingest')
async def ingest_logs(request: Request,db:Session=Depends(get_db)):
    log_objects=[]
    body = await request.body()
    text = body.decode("utf-8")

    lines = text.splitlines()

    count = 0

    for line in lines:
        if not line.strip():
            continue

        log = json.loads(line)

        log["ingested_at"] = datetime.now(timezone.utc).isoformat()
        log_objects.append({"timestamp": datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00")),"ingested_at":datetime.fromisoformat(log["ingested_at"].replace("Z", "+00:00")),"service":log["service"],"host":log["host"],"client_ip":log["client_ip"],"endpoint":log["endpoint"],"method":log["method"],"status_code":log["status_code"],"response_time_ms":log["response_time_ms"],"user_agent":log["user_agent"],"bytes_in":log["bytes_in"],"bytes_out":log["bytes_out"]})
        
        write_log(log)
        
        
        
        count += 1
    db.bulk_insert_mappings(Log,log_objects)
    db.commit()
    logs_ingested_total.inc(count)
    return {
        "status": "ok",
        "logs_ingested": count
    }



@app.get("/health")
def health():

    return {"status": "healthy"}


@app.get("/detections")
def get_detections(attack_type:Optional[str]=None,severity:Optional[str]=None,start_time:Optional[datetime]=None,end_time:Optional[datetime]=None,limit:int=Query(default=50,le=500),db:Session=Depends(get_db)):
    query=db.query(Detection)
    if attack_type:
        query=query.filter(Detection.attack_type==attack_type)
    if severity:
        query=query.filter(Detection.severity==severity)
    if start_time:
        query=query.filter(Detection.window_start>=start_time)
    if end_time:
        query=query.filter(Detection.window_start<=end_time)
    
    detections=query.order_by(Detection.window_end.desc()).limit(limit).all()

    return detections

@app.get("/detections/stats")
def get_stats(db:Session=Depends(get_db)):
    now=datetime.now(timezone.utc)
    last_24h=now-timedelta(hours=24)
    query=db.query(Detection).filter(Detection.window_end>=last_24h)
    total_detections_24h=query.count()
    severity_counts=db.query(Detection.severity,func.count(Detection.id)).filter(Detection.window_end>=last_24h).group_by(Detection.severity).all()
    count_by_severity={severity:count for severity,count in severity_counts}
    attack_type_counts=db.query(Detection.attack_type,func.count(Detection.id)).filter(Detection.window_end>=last_24h).group_by(Detection.attack_type).all()
    count_by_attack_type={atype:count for atype,count in attack_type_counts}
    

    peak_window=db.query(Detection).filter(Detection.window_end>=last_24h).order_by(Detection.request_count.desc()).first()
    if peak_window:
    
        peak_detection_window= {
            "window_start": peak_window.window_start,
            "window_end": peak_window.window_end,
            "request_count": peak_window.request_count,
            "attack_type": peak_window.attack_type
        }
    else:
        peak_detection_window=None
    return {
        "total_last_24h": total_detections_24h,
        "count_by_severity": count_by_severity,
        "count_by_attack_type": count_by_attack_type,
        "peak_detection_window": peak_detection_window
    }


@app.get('/detections/timeline')
def get_timeline(db:Session=Depends(get_db)):
    now=datetime.now(timezone.utc)
    last_24h=now-timedelta(hours=24)
    detections=db.query(Detection).filter(Detection.window_start>=last_24h).all()
    timeline=defaultdict(int)
    for d in detections:
        minute=d.window_start.replace(second=0,microsecond=0)
        timeline[minute]+=1
    
    timeline=[{"time":t,"detections":c} for t,c in sorted(timeline.items())]
    return timeline

@app.get("/metrics")
def metrics():
        registry=CollectorRegistry()
        MultiProcessCollector(registry)
        data=generate_latest(registry)
        return Response(data,media_type=CONTENT_TYPE_LATEST)






