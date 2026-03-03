# Vigil

## Overview

Vigil is a FastAPI-based application designed for log ingestion, aggregation, and detection of anomalies or attacks. It includes multiple services and utilities to handle logs, process data, and provide insights through APIs.

## Project Structure

```
aggregation_utils.py       # Utility functions for log aggregation and feature calculation
detector.py                # Detection logic for identifying anomalies or attacks
red_team.py                # Scripts or utilities for testing the system with simulated attacks
worker.py                  # Background worker for processing tasks

__pycache__/               # Compiled Python files

data/
  app_log.jsonl            # Application logs
  detection_logs.jsonl     # Detection logs
  ingested_logs.jsonl      # Ingested logs

db/
  __init__.py              # Database package initialization
  database.py              # Database connection and session management
  init_db.py               # Database initialization script
  models.py                # SQLAlchemy models for the database
  __pycache__/             # Compiled Python files

fake_app/
  __init__.py              # Fake application package initialization
  app.py                   # Simulated application for generating logs
  __pycache__/             # Compiled Python files

ingestion_service/
  __init__.py              # Ingestion service package initialization
  main.py                  # FastAPI application for log ingestion and aggregation
  __pycache__/             # Compiled Python files
```

## Key Components

### 1. `ingestion_service/main.py`

This is the main FastAPI application that provides the following endpoints:

- **POST `/ingest`**: Ingests logs sent in the request body and stores them in the database.

- **GET `/health`**: Returns the health status of the application.
- **GET `/detections`**: Retrieves detections based on optional filters like attack type, severity, and time range.
- **GET `/detections/stats`**: Provides statistics about detections in the last 24 hours, including counts by severity and attack type, and the peak detection window.

### 2. `db/`

Contains database-related files:

- `database.py`: Manages the database connection and session.
- `init_db.py`: Initializes the database schema.
- `models.py`: Defines the SQLAlchemy models for logs and detections.

### 3. `aggregation_utils.py`

Provides utility functions for:

- Fetching logs from the database.
- Calculating features for log aggregation.
- Storing aggregated features.

### 4. `detector.py`

Implements the logic for detecting anomalies or attacks based on aggregated features.

### 5. `data/`

Stores log files:

- `app_log.jsonl`: Raw application logs.
- `detection_logs.jsonl`: Logs related to detections.
- `ingested_logs.jsonl`: Logs ingested by the system.

### 6. `fake_app/`

Contains a simulated application (`app.py`) for generating logs to test the ingestion service.

### 7. `red_team.py`

Includes scripts or utilities for testing the system with simulated attacks.

### 8. `worker.py`

Handles background tasks for processing logs or other asynchronous operations.

## Environment Setup

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd vigil
   ```

2. **Set Up Python Environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   Create a `.env` file in the root directory and define the following variables:

   ```env
   INGESTED_LOGFILE_PATH=data/ingested_logs.jsonl
   DATABASE_URL=sqlite:///./db.sqlite3
   ```

4. **Initialize the Database**

   ```bash
   python db/init_db.py
   ```

5. **Run the Application**
   ```bash
   uvicorn ingestion_service.main:app --reload
   ```

## Usage

- Use tools like `curl` or Postman to interact with the API endpoints.
- Monitor logs and detections through the provided endpoints.
