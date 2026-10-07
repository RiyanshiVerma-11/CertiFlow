from app.services.job_service import JobService


def test_create_bulk_job_success(client):
    payload = {
        "title": "Aereo Cloud Drone Survey Engineer",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Riyanshi Sharma", "email": "riyanshi@example.com", "custom_note": "Top Rank"},
            {"name": "Alex Mercer", "email": "alex@example.com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202

    data = response.json()
    assert "job_id" in data
    assert data["total_recipients"] == 2
    assert data["status"] == "PENDING"
    assert f"/api/v1/jobs/{data['job_id']}" in data["status_url"]


def test_job_processing_lifecycle(client, db_session):
    payload = {
        "title": "Aereo AI Specialist",
        "issuer_name": "Aereo",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Test status initial polling
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["total"] == 2

    # Process job synchronously in test context
    # Note: TestClient runs background tasks when the client context exits,
    # or we can inspect directly:
    status_resp_after = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp_after.status_code == 200
    data = status_resp_after.json()
    assert data["status"] in ["PROCESSING", "COMPLETED"]


def test_get_non_existent_job_returns_404(client):
    response = client.get("/api/v1/jobs/non-existent-uuid-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_csv_upload_job_success(client):
    csv_content = (
        "name,email,custom_note\n"
        "Sarah Connor,sarah@skynet.com,Honor Roll\n"
        "John Connor,john@skynet.com,Distinction\n"
    )
    files = {"file": ("test_recipients.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {
        "title": "Cyber Systems Specialist",
        "issuer_name": "Defense Academy",
        "issue_date": "2026-10-07",
    }
    response = client.post("/api/v1/jobs/upload-csv", data=data, files=files)
    assert response.status_code == 202
    res_json = response.json()
    assert res_json["total_recipients"] == 2
    assert "job_id" in res_json
