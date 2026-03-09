from prometheus_client import Counter,Histogram,Gauge

logs_ingested_total=Counter('logs_ingested_total','Total logs ingested')
detections_total=Counter('detections_total','Total Detections',["attack_type","severity"])
feature_windows_processed_total=Counter('feature_windows_processed_total','Total aggregation windows processed')

detector_latency_seconds=Histogram("detector_latency_seconds","Detection execution latency")

pipeline_lag_seconds=Gauge('pipeline_lag_seconds','Delay between log timestamp and processing')



