# 🎙️ AEREO Technical Interview Preparation & Code Defense Guide

This document prepares you for technical interviews and live-coding rounds with the AEREO engineering team for this assessment submission.

---

## 📌 1. Walk Me Through Your Architecture (30-Second Elevator Pitch)

> *"I built a bulk certificate generation service using **Python**, **FastAPI**, **SQLAlchemy 2.0**, and **ReportLab**.*
>
> *When a client submits a bulk batch (via JSON or CSV), the API immediately returns `202 Accepted` with a `job_id` and schedules generation asynchronously in the background. This ensures HTTP connections never time out for large batches.*
>
> *During processing, each recipient is protected by an isolated error boundary. If a single recipient has an invalid email format or triggers an unexpected rendering exception, that record is isolated as `FAILED` with diagnostic logs, while all valid recipients generate successfully (`PARTIAL_SUCCESS`).*
>
> *Certificates are rendered as high-resolution 300-DPI vector PDFs with dynamic typography scaling and embedded QR verification codes. Clients can poll progress via `GET /jobs/{id}`, retrieve certificates individually, or stream them as an on-demand in-memory ZIP archive without disk bloat.*
>
> *The project runs locally with zero external dependencies using SQLite and FastAPI BackgroundTasks, but is architected to scale horizontally with PostgreSQL and Redis queue workers."*

---

## ❓ 2. Core Technical Questions & How to Answer Them

### Q1: Why did you choose Asynchronous (`202 Accepted`) over Synchronous?
- **Answer:** 
  *"Generating high-resolution vector PDFs is CPU- and I/O-intensive. Rendering a batch of 100+ certificates takes several seconds. A synchronous endpoint would hold the client's HTTP connection open, creating risk of `504 Gateway Timeout` behind load balancers/reverse proxies (like Nginx or AWS ALB) and blocking worker threads. Returning `202 Accepted` immediately gives the client a tracking identifier to poll progress or subscribe to webhooks, which follows REST standards for bulk computational workloads."*

### Q2: Why ReportLab instead of HTML-to-PDF tools like Playwright, Puppeteer, or wkhtmltopdf?
- **Answer:**
  *"Headless Chromium or WebKit browsers introduce massive operational overhead: 200MB+ container bloat, native OS dependencies (e.g., libXcomposite, libfontconfig), and high memory consumption (~80-120MB per browser instance). ReportLab is pure Python, starts instantaneously, executes in under 25ms per certificate, and renders true vector paths that remain crisp at 300 DPI without needing external browser binaries."*

### Q3: How does your Fault Isolation work? Why not reject the whole batch?
- **Answer:**
  *"In real-world event operations, batch uploads regularly contain dirty records (e.g. `user@invalid`, blank names). Rejecting an entire 500-person batch because row 47 is corrupt creates high user friction. I implemented two layers of protection:*
  1. *Ingest-time validation: `validate_recipient_data()` flags invalid records upfront as `FAILED` with clear error reasons without aborting the batch.*
  2. *Runtime execution boundary: inside `process_bulk_job()`, each certificate generation is wrapped in a `try/except` block. If any unexpected error occurs, it transitions only that certificate to `FAILED`, updates `job.failures`, and continues processing the rest of the batch.*
  *The job status accurately reflects the outcome (`COMPLETED`, `PARTIAL_SUCCESS`, or `FAILED`)."*

### Q4: How do you handle SQLite concurrency issues?
- **Answer:**
  *"SQLite has a file-level database lock on writes. Committing on every single loop iteration across 500 recipients creates disk I/O bottlenecks and `OperationalError: database is locked`. I addressed this with **batched commits** (`settings.BATCH_COMMIT_SIZE = 20`) and retry backoff. In production, changing `DATABASE_URL` connects directly to PostgreSQL which uses row-level locking (MVCC) and connection pooling."*

### Q5: How does the ZIP download avoid disk starvation?
- **Answer:**
  *"Instead of building and persisting a physical ZIP file on disk for every download request—which would duplicate storage and require disk cleanup crons—`ZipService` uses `io.BytesIO` and Python's `zipfile` module with FastAPI's `StreamingResponse`. The archive is generated as an in-memory stream directly to the HTTP socket, achieving zero disk footprint."*

---

## 🛠️ 3. Anticipated Live-Coding Modifications (How to Code Them Fast)

During the interview, the interviewer may ask you to modify the application on the spot. Here are the most likely tasks:

### Task A: "Make the certificate generation synchronous instead of background"
- **Where to change:** In `app/api/v1/endpoints/jobs.py` under `create_bulk_job()`:
- **Change:** Instead of `dispatcher.dispatch(job.id, background_tasks)`, directly invoke:
  ```python
  JobService.process_bulk_job(job.id)
  ```
  And change response code to `status.HTTP_200_OK` returning `JobService.get_job_status(db, job.id)`.

### Task B: "Add a new field to the certificate (e.g., 'Grade' or 'Score')"
1. **Schema:** In `app/schemas/certificate.py`, add `grade: Optional[str] = None` to `RecipientInput`.
2. **Model:** In `app/models/certificate.py`, add `grade = Column(String(50), nullable=True)`.
3. **Generator:** In `app/services/certificate_generator.py`, add `grade` to `generate_pdf_bytes()` and draw it on the canvas:
   ```python
   if grade:
       c.setFont("Helvetica-Bold", 12)
       c.setFillColor(cls.COLOR_GOLD)
       c.drawCentredString(cls.PAGE_WIDTH / 2, y - 25, f"Grade: {grade}")
   ```

### Task C: "Add an expiration date or certificate status check"
- Already built! Point to `GET /api/v1/certificates/verify/{certificate_code}` which queries the credential database, checks authenticity, and returns verification status and timestamps.

---

## 📊 4. Known Trade-Offs & Production Scaling Roadmap

If the interviewer asks: *"What are the limitations of this current code, and how would you evolve it for 100,000 certificates a day?"*

1. **Distributed Worker Nodes:** Currently defaults to in-process background tasks. For 100K/day, switch to `TASK_QUEUE_BACKEND="redis"` where containerized Celery/RQ workers consume off Redis queues across Kubernetes pods.
2. **Object Storage:** Currently defaults to local storage for zero-dependency evaluation. In cloud production, set `STORAGE_BACKEND="s3"` so PDFs stream directly to AWS S3 / Cloudflare R2 with presigned download URLs.
3. **Database Migration:** Switch from SQLite to PostgreSQL with read replicas for status queries and PgBouncer for connection pooling.
