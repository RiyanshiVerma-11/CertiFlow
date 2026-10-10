from app.services.job_service import JobService
from app.models.job import JobStatus, GenerationJob
from app.models.certificate import Certificate, CertificateStatus


def test_individual_recipient_failure_does_not_abort_batch(client, db_session):
    payload = {
        "title": "Aereo Systems Reliability Exam",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "Faulty Recipient", "email": "invalid-email-format"},
            {"name": "Valid Recipient Two", "email": "valid2@example.com"},
        ],
    }

    # 1. Submit batch (TestClient automatically executes BackgroundTasks on request completion)
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # 2. Query job telemetry
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    # Crucial assertion: Job is PARTIAL_SUCCESS, NOT completely failed
    assert status_data["status"] == "PARTIAL_SUCCESS"
    assert status_data["total"] == 3
    assert status_data["processed"] == 3
    assert status_data["successful"] == 2
    assert status_data["failed"] == 1

    # Check failure details
    assert len(status_data["failures"]) == 1
    failure = status_data["failures"][0]
    assert failure["recipient_name"] == "Faulty Recipient"
    assert failure["recipient_email"] == "invalid-email-format"
    assert "invalid email address format" in failure["error"].lower()

    # Check individual certificates in DB
    certs_data = client.get(f"/api/v1/jobs/{job_id}/certificates").json()
    certs = certs_data["items"]
    assert len(certs) == 3
    success_certs = [c for c in certs if c["status"] == "SUCCESS"]
    failed_certs = [c for c in certs if c["status"] == "FAILED"]

    assert len(success_certs) == 2
    assert len(failed_certs) == 1
    assert failed_certs[0]["download_url"] is None
    assert success_certs[0]["download_url"] is not None


def test_real_dirty_data_zero_drop_fault_isolation(client):
    """
    Validates genuine zero-drop fault isolation with real-world dirty data:
    Invalid email formatting and whitespace names are isolated per-record
    without rejecting the entire batch at the HTTP gateway!
    """
    payload = {
        "title": "Aereo Cloud Ingestion Reliability",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "Broken Email Recipient", "email": "bad-email@"},
            {"name": "   ", "email": "blank_name@example.com"},
            {"name": "Valid Recipient Two", "email": "valid2@example.com"},
        ],
    }

    # HTTP Gateway accepts the batch with zero-drop guarantee
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Verify telemetry
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "PARTIAL_SUCCESS"
    assert data["total"] == 4
    assert data["processed"] == 4
    assert data["successful"] == 2
    assert data["failed"] == 2

    # Check that error details identify the exact bad data
    failure_reasons = [f["error"] for f in data["failures"]]
    assert any("bad-email@" in r or "email" in r.lower() for r in failure_reasons)
    assert any("name cannot be empty" in r.lower() for r in failure_reasons)

    # Check certificates list
    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    certs = certs_resp.json()["items"]
    assert len(certs) == 4
    successes = [c for c in certs if c["status"] == "SUCCESS"]
    failures = [c for c in certs if c["status"] == "FAILED"]
    assert len(successes) == 2
    assert len(failures) == 2


def test_csv_upload_zero_drop_dirty_data(client):
    """
    Validates that a CSV upload with formatting errors on specific rows
    processes all valid rows and isolates the dirty rows without returning 422!
    """
    csv_content = (
        "name,email\n"
        "Valid Recipient,valid@domain.com\n"
        "Dirty Row Recipient,bad-email@\n"
        "Another Valid,another@domain.com\n"
    )
    files = {"file": ("recipients_with_errors.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {
        "title": "Aereo CSV Fault Tolerance",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
    }
    response = client.post("/api/v1/jobs/upload-csv", data=data, files=files)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    status_data = status_resp.json()
    assert status_data["total"] == 3
    assert status_data["successful"] == 2
    assert status_data["failed"] == 1
    assert status_data["status"] == "PARTIAL_SUCCESS"


def test_runtime_pdf_rendering_exception_fault_isolation(client, monkeypatch):
    """
    Validates that if an unexpected exception occurs during PDF generation (e.g., ReportLab
    canvas error or OS I/O error), the single failing certificate is caught at the error
    boundary and the remaining batch completes successfully.
    """
    from app.services.certificate_generator import CertificateGenerator

    original_generate = CertificateGenerator.generate_pdf_bytes

    def flaky_generate(**kwargs):
        if kwargs.get("recipient_name") == "Crash Candidate":
            raise RuntimeError("Simulated ReportLab vector canvas crash")
        return original_generate(**kwargs)

    monkeypatch.setattr(CertificateGenerator, "generate_pdf_bytes", flaky_generate)

    payload = {
        "title": "Runtime Crash Resilience",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "Crash Candidate", "email": "crash@example.com"},
            {"name": "Valid Recipient Two", "email": "valid2@example.com"},
        ],
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    assert status_data["status"] == "PARTIAL_SUCCESS"
    assert status_data["total"] == 3
    assert status_data["successful"] == 2
    assert status_data["failed"] == 1
    assert "Simulated ReportLab vector canvas crash" in status_data["failures"][0]["error"]

