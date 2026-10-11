# 🎓 CertiFlow — Bulk Certificate Generator Service

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://certiflow-w2h9.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red)](https://www.sqlalchemy.org)
[![Tests](https://img.shields.io/badge/Tests-34%20Passed%20(100%25)-brightgreen)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> 🌐 **Live Demo Application:** [https://certiflow-w2h9.onrender.com](https://certiflow-w2h9.onrender.com)  
> 📖 **Interactive OpenAPI / Swagger UI:** [https://certiflow-w2h9.onrender.com/docs](https://certiflow-w2h9.onrender.com/docs)  
> **A high-volume certificate generation, status tracking, and retrieval service built with Python, FastAPI, SQLAlchemy, and ReportLab.**  
> *Developed for the AEREO Software Development Engineer (SDE) Assessment.*

---

## 📑 Table of Contents
1. [Overview & Requirements Coverage](#-overview--requirements-coverage)
2. [Quickstart Guide](#-quickstart-guide)
3. [Core Architectural Decisions](#-core-architectural-decisions)
4. [API Specification & Examples](#-api-specification--examples)
5. [Validation & Fault Isolation Strategy](#-validation--fault-isolation-strategy)
6. [Interactive Testing Console](#-interactive-testing-console)
7. [Automated Testing Suite](#-automated-testing-suite)
8. [Optional Production Extensions](#-optional-production-extensions)

---

## 🚀 Overview & Requirements Coverage

This application addresses the problem of bulk certificate generation for events, courses, and training programs:
- **Bulk Ingestion:** Accepts requests with event details and a list of recipients via JSON (`POST /api/v1/jobs`) or CSV file upload (`POST /api/v1/jobs/upload-csv`).
- **Asynchronous Execution:** Returns an immediate `202 Accepted` response with a unique `job_id`, delegating certificate generation to background workers so client HTTP connections are never blocked.
- **Single Vector Template:** Generates 300-DPI vector PDF certificates using pure-Python ReportLab with dynamic font scaling, recipient details, issue dates, and embedded verification QR codes.
- **Per-Record Fault Isolation:** If an individual recipient contains malformed data (invalid email syntax, missing name) or triggers a rendering error, that specific record is flagged as `FAILED` with diagnostics while valid recipients succeed (`PARTIAL_SUCCESS`). The batch is never aborted.
- **Progress Tracking & Telemetry:** Clients can poll `GET /api/v1/jobs/{job_id}` to inspect real-time progress percentages, success/failure counts, and granular error details.
- **Retrieval:** Certificates can be retrieved individually as PDF (`GET /api/v1/certificates/{id}/download`), listed with pagination (`GET /api/v1/jobs/{id}/certificates`), or downloaded as an in-memory streamed ZIP archive (`GET /api/v1/jobs/{id}/download-zip`).

---

## 💻 Quickstart Guide

> **Zero External Dependencies Required:** You do **not** need Redis, Docker, or PostgreSQL to evaluate this application. It runs out of the box using SQLite and standard in-memory background processing.

### 1. Setup & Installation
```bash
# Clone the repository
git clone https://github.com/RiyanshiVerma-11/CertiFlow.git
cd certiflow

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Test Suite
```bash
python -m pytest -v
```
*(All 34 tests execute in ~4.5 seconds with zero external dependencies).*

### 3. Start the Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Interactive Testing Console:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧠 Core Architectural Decisions

### 1. Asynchronous (`202 Accepted`) vs. Synchronous Processing
- **Decision:** Asynchronous background processing returning `202 Accepted`.
- **Reasoning:** Generating 100+ high-resolution PDFs takes several seconds. A synchronous request would block the client connection, risk HTTP 504 timeouts behind reverse proxies, and starve ASGI worker threads. The asynchronous pattern with polling provides responsive UX and adheres to bulk REST conventions.

### 2. Pure-Python Vector Engine (ReportLab) vs. Headless Browsers
- **Decision:** ReportLab vector canvas rendering.
- **Reasoning:** Headless browsers (Puppeteer, Playwright, wkhtmltopdf) introduce 200MB+ container dependencies, native C-library compilation issues, and significant memory overhead (~100MB per browser instance). ReportLab runs pure Python, executes in <25ms per certificate, and generates crisp 300-DPI vector PDFs without external binaries.

### 3. Database Layer: SQLAlchemy 2.0 with SQLite / PostgreSQL Portability
- **Decision:** SQLAlchemy 2.0 ORM configured for SQLite by default, configurable to PostgreSQL via `DATABASE_URL`.
- **Reasoning:** Enables zero-setup local evaluation without needing a running database server, while remaining production-ready for connection-pooled PostgreSQL deployments.

### 4. Per-Record Fault Isolation Boundary
- **Decision:** Ingest-time schema checks and per-item `try/catch` execution blocks.
- **Reasoning:** Enterprise bulk uploads regularly include bad records (e.g., misspelled emails, empty names). Failing an entire 500-recipient batch because row 47 is corrupt is unacceptable. CertiFlow isolates failures per record and records detailed diagnostics in `job.failures`.

### 5. In-Memory Streaming ZIP vs. Disk Buffering
- **Decision:** Streamed in-memory ZIP generation via `io.BytesIO` and `StreamingResponse`.
- **Reasoning:** Storing pre-zipped archives on disk creates redundant storage bloat. Generating ZIP streams on-demand saves disk space and eliminates stale file cleanup issues.

---

## 📡 API Specification & Examples

### 1. Submit Bulk Job (JSON)
- **POST** `/api/v1/jobs` (`202 Accepted`)

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Drone Photogrammetry Specialist",
    "issuer_name": "Aereo Academy",
    "issue_date": "2026-10-07",
    "recipients": [
      {
        "name": "Riyanshi Verma",
        "email": "riyanshi@example.com",
        "custom_note": "Distinction • Rank 1"
      },
      {
        "name": "Alex Mercer",
        "email": "alex@example.com"
      }
    ]
  }'
```

**Response:**
```json
{
  "job_id": "3c829e0a-bf41-4773-8bc6-37ff4d3b84f3",
  "status": "PENDING",
  "total_recipients": 2,
  "message": "Bulk certificate generation job accepted (FastAPI BackgroundTasks).",
  "status_url": "/api/v1/jobs/3c829e0a-bf41-4773-8bc6-37ff4d3b84f3"
}
```

---

### 2. Submit Bulk Job via CSV Upload
- **POST** `/api/v1/jobs/upload-csv` (`202 Accepted`)

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/upload-csv" \
  -F "file=@data/sample_recipients.csv" \
  -F "title=Drone Photogrammetry Specialist" \
  -F "issuer_name=Aereo Academy" \
  -F "issue_date=2026-10-07"
```

---

### 3. Check Job Status & Progress Telemetry
- **GET** `/api/v1/jobs/{job_id}` (`200 OK`)

```bash
curl "http://localhost:8000/api/v1/jobs/3c829e0a-bf41-4773-8bc6-37ff4d3b84f3"
```

**Response:**
```json
{
  "job_id": "3c829e0a-bf41-4773-8bc6-37ff4d3b84f3",
  "title": "Drone Photogrammetry Specialist",
  "issuer_name": "Aereo Academy",
  "issue_date": "2026-10-07",
  "status": "COMPLETED",
  "progress_percentage": 100.0,
  "total": 2,
  "processed": 2,
  "successful": 2,
  "failed": 0,
  "failures": [],
  "certificates_url": "/api/v1/jobs/3c829e0a-bf41-4773-8bc6-37ff4d3b84f3/certificates",
  "zip_download_url": "/api/v1/jobs/3c829e0a-bf41-4773-8bc6-37ff4d3b84f3/download-zip",
  "created_at": "2026-10-07T14:00:00Z",
  "updated_at": "2026-10-07T14:00:01Z"
}
```

---

### 4. Retrieve Individual Certificate PDF
- **GET** `/api/v1/certificates/{id}/download?disposition=inline|attachment`

```bash
# View inline in browser tab:
curl "http://localhost:8000/api/v1/certificates/<CERT_ID>/download?disposition=inline"

# Download as file attachment:
curl -O -J "http://localhost:8000/api/v1/certificates/<CERT_ID>/download"
```

---

### 5. Download All Certificates as ZIP
- **GET** `/api/v1/jobs/{job_id}/download-zip`

```bash
curl -O -J "http://localhost:8000/api/v1/jobs/<JOB_ID>/download-zip"
```

---

### 6. Verify Certificate Authenticity
- **GET** `/api/v1/certificates/verify/{certificate_code}`

```bash
curl "http://localhost:8000/api/v1/certificates/verify/CERT-A1B2C3D4"
```

---

## 🛡️ Validation & Fault Isolation Strategy

1. **Pre-Ingestion Validation:** Email syntax and name requirements are validated per recipient. Malformed records are tagged as `FAILED` with explicit error descriptions (`"Validation Error: Invalid email address format"`) without halting the rest of the batch.
2. **Runtime Generation Isolation:** During PDF canvas rendering, each item executes inside an isolated `try/except` boundary. Any unexpected exception (e.g., rendering error, character encoding issue) transitions only that specific certificate to `FAILED`, allowing other certificates to complete.
3. **Transparent Reporting:** The final job status accurately reflects outcomes:
   - `COMPLETED`: All recipients succeeded.
   - `PARTIAL_SUCCESS`: Some recipients succeeded, failures isolated with diagnostic logs.
   - `FAILED`: No valid recipients could be processed.

---

## 🖥️ Interactive Testing Console

For quick visual testing, an interactive console is available at `http://localhost:8000/`:
- **Load Demo Batch:** Pre-populates a sample batch including a malformed record to demonstrate fault isolation.
- **Progress Tracking:** Live polling with progress bar and success/failure counters.
- **PDF Inspection:** Direct links to view generated vector PDFs in a browser tab or download as ZIP.
- **Verification Portal:** Look up any certificate code to verify its authenticity and metadata.

---

## 🧪 Automated Testing Suite

The test suite covers all requirements outlined in the assessment rubric:

```bash
python -m pytest -v
```

### Test Coverage Breakdown (34 Tests / 100% Passing):
| Test File | Focus Area | Status |
| :--- | :--- | :--- |
| `tests/test_jobs.py` | Job submission (JSON & CSV), 202 Accepted, status polling | ✅ **PASSED** |
| `tests/test_validation.py` | Empty batches, missing titles, invalid file types, CSV headers | ✅ **PASSED** |
| `tests/test_generator.py` | ReportLab vector PDF integrity, dynamic text scaling | ✅ **PASSED** |
| `tests/test_fault_isolation.py` | Per-record dirty data isolation, runtime crash boundaries | ✅ **PASSED** |
| `tests/test_retrieval.py` | Individual PDF downloads, streamed in-memory ZIP archive | ✅ **PASSED** |
| `tests/test_pagination.py` | Limit/offset pagination and status filtering on certificate list | ✅ **PASSED** |
| `tests/test_lifecycle_cleanup.py` | Storage retention garbage collection, streaming memory safety | ✅ **PASSED** |
| `tests/test_storage_abstraction.py` | Local and cloud storage provider contracts | ✅ **PASSED** |
| `tests/test_task_queue_and_recovery.py` | Worker queue abstraction, container crash recovery | ✅ **PASSED** |
| `tests/test_rate_limiter.py` | Sliding window rate limiting logic and brute force protection | ✅ **PASSED** |
| `tests/test_email_dispatch.py` | Asynchronous email dispatch with PDF attachment | ✅ **PASSED** |

---

## 🔌 Optional Production Extensions

The codebase is structured to scale cleanly for production deployments:
1. **Docker Compose (`docker-compose.yml`):** Multi-service orchestration including FastAPI API gateway, dedicated Redis worker (`app.worker`), Redis 7, and PostgreSQL 16.
2. **Decoupled Task Queue:** Set `TASK_QUEUE_BACKEND="redis"` to offload jobs to an external Redis queue.
3. **Cloud Storage Provider:** Set `STORAGE_BACKEND="s3"` to store certificates in AWS S3 or MinIO.
4. **Automated Email Delivery:** Set `EMAIL_DISPATCH_ENABLED=true` to automatically deliver certificates via SMTP or AWS SES upon job completion.

---

## 👤 Submission Details
- **Role:** Software Development Engineer (SDE) Assessment
- **Company:** AEREO (Bangalore)
- **Candidate:** Riyanshi Verma
