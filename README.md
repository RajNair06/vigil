# Vigil 🛡️

**Real-time log ingestion, feature aggregation, and attack detection system built with FastAPI.**

Vigil continuously ingests HTTP access logs, aggregates them into time-windowed feature sets, and classifies attack patterns including DDoS, brute force, vulnerability scanning, and resource exhaustion — all queryable via REST API with Prometheus metrics.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Detection Logic](#detection-logic)
- [API Reference](#api-reference)
- [Metrics](#metrics)
- [Setup & Installation](#setup--installation)
- [Running the System](#running-the-system)
- [Red Team Testing](#red-team-testing)

---

## Architecture

```
                    ┌─────────────────┐
   HTTP Logs ──────▶│  POST /ingest   │──▶ PostgreSQL / SQLite
                    └─────────────────┘         │
                                                 │
                    ┌─────────────────┐          │
                    │  worker.py      │◀─────────┘
                    │  (every 5s)     │
                    │  - fetch logs   │
                    │  - calc features│
                    │  - run detector │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  detector.py    │──▶ detections table
                    │  classify_attack│──▶ detection_logs.jsonl
                    └─────────────────┘
                    
   GET /detections, /detections/stats, /detections/timeline ──▶ Query detections
   GET /metrics ──▶ Prometheus scrape endpoint
```

---

## Project Structure

```
vigil/
├── main.py                   # FastAPI app — ingest + query endpoints
├── worker.py                 # Background aggregation + detection loop
├── detector.py               # Attack classification logic
├── aggregation_utils.py      # Feature extraction from log windows
├── metrics.py                # Prometheus counters, histograms, gauges
├── red_team.py               # Simulated attack traffic generator
│
├── db/
│   ├── database.py           # SQLAlchemy engine + session
│   ├── models.py             # Log, Feature, Detection ORM models
│   └── init_db.py            # Schema initializer
│
├── fake_app/
│   └── app.py                # Random log generator (baseline traffic)
│
└── data/
    ├── ingested_logs.jsonl   # Raw ingested log archive
    └── detection_logs.jsonl  # Detection event log archive
```

---

## Detection Logic

The worker runs every **5 seconds**, aggregating logs from the current time window. Features are extracted and passed to `classify_attack()`:

| Attack Type          | Trigger Conditions                                                                 | Severity |
|----------------------|------------------------------------------------------------------------------------|----------|
| `DDOS`               | `request_count > 500` AND `unique_ips > 200` AND `error_ratio < 0.2`              | HIGH     |
| `BRUTE_FORCE`        | `error_ratio > 0.6` AND `unique_ips < 20` AND `unique_endpoints < 5`              | HIGH     |
| `VULNERABILITY_SCAN` | `unique_endpoints > 50` AND `unique_ips > 50`                                      | MEDIUM   |
| `RESOURCE_EXHAUSTION`| `avg_response_time > 2000ms` AND `request_count > 200`                            | MEDIUM   |

---

## API Reference

### `POST /ingest`

Ingests a batch of newline-delimited JSON logs.

**Request**
```
Content-Type: text/plain

{"timestamp":"2024-01-15T10:30:00Z","service":"api","host":"web-01","client_ip":"192.168.1.100","endpoint":"/api/users","method":"GET","status_code":200,"response_time_ms":45,"user_agent":"Mozilla/5.0","bytes_in":512,"bytes_out":2048}
{"timestamp":"2024-01-15T10:30:01Z","service":"api","host":"web-01","client_ip":"10.0.0.5","endpoint":"/api/login","method":"POST","status_code":401,"response_time_ms":120,"user_agent":"curl/7.68.0","bytes_in":256,"bytes_out":64}
```

**Response**
```json
{
  "status": "ok",
  "logs_ingested": 2
}
```

---

### `GET /health`

Returns service health status.

**Response**
```json
{
  "status": "healthy"
}
```

---

### `GET /detections`

Returns recent detections with optional filters.

**Query Parameters**

| Parameter    | Type     | Description                                           |
|--------------|----------|-------------------------------------------------------|
| `attack_type`| string   | Filter by type: `DDOS`, `BRUTE_FORCE`, `VULNERABILITY_SCAN`, `RESOURCE_EXHAUSTION` |
| `severity`   | string   | Filter by severity: `HIGH`, `MEDIUM`                  |
| `start_time` | datetime | Filter detections at or after this time (ISO 8601)    |
| `end_time`   | datetime | Filter detections at or before this time (ISO 8601)   |
| `limit`      | int      | Max results to return (default: `50`, max: `500`)     |

**Sample Output — No filters (default)**
```json
[
  {
    "id": 42,
    "window_start": "2024-01-15T10:25:00+00:00",
    "window_end": "2024-01-15T10:30:00+00:00",
    "attack_type": "DDOS",
    "severity": "HIGH",
    "request_count": 3204
  },
  {
    "id": 41,
    "window_start": "2024-01-15T09:55:00+00:00",
    "window_end": "2024-01-15T10:00:00+00:00",
    "attack_type": "BRUTE_FORCE",
    "severity": "HIGH",
    "request_count": 980
  }
]
```

**Sample Output — `?attack_type=BRUTE_FORCE`**
```json
[
  {
    "id": 41,
    "window_start": "2024-01-15T09:55:00+00:00",
    "window_end": "2024-01-15T10:00:00+00:00",
    "attack_type": "BRUTE_FORCE",
    "severity": "HIGH",
    "request_count": 980
  },
  {
    "id": 38,
    "window_start": "2024-01-15T08:10:00+00:00",
    "window_end": "2024-01-15T08:15:00+00:00",
    "attack_type": "BRUTE_FORCE",
    "severity": "HIGH",
    "request_count": 1150
  }
]
```

**Sample Output — `?attack_type=VULNERABILITY_SCAN&severity=MEDIUM`**
```json
[
  {
    "id": 37,
    "window_start": "2024-01-15T07:45:00+00:00",
    "window_end": "2024-01-15T07:50:00+00:00",
    "attack_type": "VULNERABILITY_SCAN",
    "severity": "MEDIUM",
    "request_count": 215
  }
]
```

**Sample Output — `?severity=HIGH&start_time=2024-01-15T08:00:00Z&end_time=2024-01-15T11:00:00Z`**
```json
[
  {
    "id": 42,
    "window_start": "2024-01-15T10:25:00+00:00",
    "window_end": "2024-01-15T10:30:00+00:00",
    "attack_type": "DDOS",
    "severity": "HIGH",
    "request_count": 3204
  },
  {
    "id": 41,
    "window_start": "2024-01-15T09:55:00+00:00",
    "window_end": "2024-01-15T10:00:00+00:00",
    "attack_type": "BRUTE_FORCE",
    "severity": "HIGH",
    "request_count": 980
  }
]
```

**Sample Output — `?attack_type=RESOURCE_EXHAUSTION`**
```json
[
  {
    "id": 35,
    "window_start": "2024-01-15T06:30:00+00:00",
    "window_end": "2024-01-15T06:35:00+00:00",
    "attack_type": "RESOURCE_EXHAUSTION",
    "severity": "MEDIUM",
    "request_count": 312
  }
]
```

---

### `GET /detections/stats`

Returns aggregated detection statistics for the **last 24 hours**.

**Response**
```json
{
  "total_last_24h": 14,
  "count_by_severity": {
    "HIGH": 9,
    "MEDIUM": 5
  },
  "count_by_attack_type": {
    "DDOS": 4,
    "BRUTE_FORCE": 5,
    "VULNERABILITY_SCAN": 3,
    "RESOURCE_EXHAUSTION": 2
  },
  "peak_detection_window": {
    "window_start": "2024-01-15T10:25:00+00:00",
    "window_end": "2024-01-15T10:30:00+00:00",
    "request_count": 3204,
    "attack_type": "DDOS"
  }
}
```

---

### `GET /detections/timeline`

Returns per-minute detection counts for the **last 24 hours**, suitable for charting.

**Response**
```json
[
  { "time": "2024-01-15T08:10:00+00:00", "detections": 1 },
  { "time": "2024-01-15T09:55:00+00:00", "detections": 2 },
  { "time": "2024-01-15T10:25:00+00:00", "detections": 3 },
  { "time": "2024-01-15T10:26:00+00:00", "detections": 1 }
]
```

---

### `GET /metrics`

Exposes Prometheus metrics for scraping. Returns plain text in the Prometheus exposition format.

```
# HELP logs_ingested_total Total logs ingested
# TYPE logs_ingested_total counter
logs_ingested_total 48231.0

# HELP detections_total Total Detections
# TYPE detections_total counter
detections_total{attack_type="DDOS",severity="HIGH"} 4.0
detections_total{attack_type="BRUTE_FORCE",severity="HIGH"} 5.0
detections_total{attack_type="VULNERABILITY_SCAN",severity="MEDIUM"} 3.0

# HELP detector_latency_seconds Detection execution latency
# TYPE detector_latency_seconds histogram
detector_latency_seconds_bucket{le="0.005"} 142.0
detector_latency_seconds_sum 0.312
detector_latency_seconds_count 150.0

# HELP feature_windows_processed_total Total aggregation windows processed
# TYPE feature_windows_processed_total counter
feature_windows_processed_total 150.0

# HELP pipeline_lag_seconds Delay between log timestamp and processing
# TYPE pipeline_lag_seconds gauge
pipeline_lag_seconds 1.23
```

---

## Metrics

Vigil tracks the following Prometheus metrics (defined in `metrics.py`):

| Metric                          | Type      | Description                                    |
|---------------------------------|-----------|------------------------------------------------|
| `logs_ingested_total`           | Counter   | Total number of log lines ingested             |
| `detections_total`              | Counter   | Total detections, labeled by `attack_type` and `severity` |
| `feature_windows_processed_total` | Counter | Number of aggregation windows completed        |
| `detector_latency_seconds`      | Histogram | Time taken to run `classify_attack()`          |
| `pipeline_lag_seconds`          | Gauge     | Lag between log event time and processing time |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vigil
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Log file paths
INGESTED_LOGFILE_PATH=data/ingested_logs.jsonl
DETECTION_LOGFILE_PATH=data/detection_logs.jsonl

# Database
DATABASE_URL=sqlite:///./vigil.db

# Ingest URL (used by red_team.py and fake_app)
INGEST_URL=http://localhost:8000/ingest
```

### 4. Initialize the Database

```bash
python db/init_db.py
```

### 5. Create Prometheus Multiprocess Directory

```bash
mkdir -p /tmp/prometheus
```

---

## Running the System

Vigil has two processes that should run concurrently: the **API server** and the **background worker**.

### Start the API Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start the Background Worker

In a separate terminal:

```bash
python worker.py
```

The worker runs a continuous loop (every 5 seconds) that:
1. Fetches logs from the current time window
2. Calculates aggregate features (request count, error ratio, unique IPs, etc.)
3. Stores features to the database
4. Runs detection and writes any findings to the `detections` table and `detection_logs.jsonl`

---

## Red Team Testing

`red_team.py` can simulate each attack type against a running Vigil instance. Uncomment the desired attack in `__main__`:

```python
# red_team.py
if __name__ == "__main__":
    ddos_attack(3000)          # 3000 req/s from 200+ IPs, low error rate
    brute_force(1000)          # 1000 requests from single IP to /api/login, 401s
    vulnerability_scan(200)    # 200 requests probing unique endpoints
    resource_exhaustion(300)   # 300 requests with 2500–5000ms response times
```

Run it with:

```bash
python red_team.py
```

> **Note:** Ensure the API server and worker are both running before executing red team scripts. Detections typically appear within one worker cycle (~5 seconds).

---

## Log Format

Vigil expects logs in JSON format, one object per line (`application/x-ndjson` or `text/plain`):

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "api",
  "host": "web-01",
  "client_ip": "192.168.1.100",
  "endpoint": "/api/users",
  "method": "GET",
  "status_code": 200,
  "response_time_ms": 45,
  "user_agent": "Mozilla/5.0 (compatible)",
  "bytes_in": 512,
  "bytes_out": 2048
}
```