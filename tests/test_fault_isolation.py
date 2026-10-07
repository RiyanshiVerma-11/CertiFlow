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
            {"name": "Faulty Recipient", "email": "faulty.__fail__@domain.com"},
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
    assert "faulty.__fail__@domain.com" in failure["recipient_email"]
    assert "forced test failure" in failure["error"].lower()

    # Check individual certificates in DB
    certs = client.get(f"/api/v1/jobs/{job_id}/certificates").json()
    assert len(certs) == 3
    success_certs = [c for c in certs if c["status"] == "SUCCESS"]
    failed_certs = [c for c in certs if c["status"] == "FAILED"]

    assert len(success_certs) == 2
    assert len(failed_certs) == 1
    assert failed_certs[0]["download_url"] is None
    assert success_certs[0]["download_url"] is not None
