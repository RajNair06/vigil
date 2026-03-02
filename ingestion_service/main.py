from fastapi import FastAPI,Request,Depends
from contextlib import asynccontextmanager
import os
import time
import threading
from pathlib import Path
import json
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.database import get_db,SessionLocal
from db.models import Log
from datetime import datetime,timezone
from aggregation_utils import fetch_logs,calculate_features,store_features,window_size
load_dotenv()
ingested_log_path=os.getenv('INGESTED_LOGFILE_PATH')
os.makedirs(os.path.dirname(Path(ingested_log_path)),exist_ok=True)


sleep_interval=10

def run_aggregator():
    
    while True:
        db=SessionLocal()

        try:
            window_end=datetime.now(timezone.utc)
            window_start=window_end-window_size
            logs=fetch_logs(db,window_start,window_end)
            feature_data=calculate_features(logs,window_start,window_end)
            if feature_data:
                store_features(db,feature_data)
                db.commit()
                print(f"aggregated {feature_data['request_count']} logs")
        finally:
            db.close()
        time.sleep(sleep_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(
        target=run_aggregator,
        daemon=True
    ).start()

    print("Aggregator started")

    yield

app=FastAPI(lifespan=lifespan)

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
        log_objects.append({"timestamp": datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00")),"ingested_at":datetime.fromisoformat(log["ingested_at"].replace("Z", "+00:00")),"service":log["service"],"host":log["host"],"endpoint":log["endpoint"],"method":log["method"],"status_code":log["status_code"],"response_time_ms":log["response_time_ms"],"user_agent":log["user_agent"],"bytes_in":log["bytes_in"],"bytes_out":log["bytes_out"]})
        
        write_log(log)
        
        
        
        count += 1
    db.bulk_insert_mappings(Log,log_objects)
    db.commit()
    return {
        "status": "ok",
        "logs_ingested": count
    }

@app.post("/aggregate")
def aggregate(db:Session=Depends(get_db)):
    window_end=datetime.now(timezone.utc)
    window_start=window_end-window_size
    logs=fetch_logs(db,window_start,window_end)
    feature_data=calculate_features(logs,window_start,window_end)
    if feature_data:
        store_features(db,feature_data)
    return {
        "status":"ok","logs_processed":len(logs)
    }

@app.get("/health")
def health():

    return {"status": "healthy"}





