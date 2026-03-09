import os
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus"
from db.database import SessionLocal
from datetime import datetime,timezone
import time
from aggregation_utils import fetch_logs,calculate_features,store_features,window_size
from detector import run_detection
from metrics import feature_windows_processed_total,detections_total
sleep_interval=5
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
                feature_windows_processed_total.inc()
                print(f"aggregated {feature_data['request_count']} logs")
                print("Calling run_detection...")
                run_detection(db)
                
            
        except Exception as e:
            print(e)
            db.rollback()
        finally:
            db.close()
            
        time.sleep(sleep_interval)

if __name__=="__main__":
    run_aggregator()
