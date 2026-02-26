from fastapi import FastAPI,Request
from pydantic import BaseModel
import os
from pathlib import Path
import json
from dotenv import load_dotenv

from datetime import datetime,timezone
load_dotenv()
ingested_log_path=os.getenv('INGESTED_LOGFILE_PATH')
os.makedirs(os.path.dirname(Path(ingested_log_path)),exist_ok=True)
app=FastAPI()



def write_log(log):
    with open(ingested_log_path,'a') as f:
        f.write(json.dumps(log) + "\n")

@app.post('/ingest')
async def ingest_logs(request: Request):

    body = await request.body()
    text = body.decode("utf-8")

    lines = text.splitlines()

    count = 0

    for line in lines:
        if not line.strip():
            continue

        log = json.loads(line)

        log["ingested_at"] = datetime.now(timezone.utc).isoformat()

        write_log(log)

        count += 1

    return {
        "status": "ok",
        "logs_ingested": count
    }
    

@app.get("/health")
def health():

    return {"status": "healthy"}





