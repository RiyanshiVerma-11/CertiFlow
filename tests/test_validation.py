def test_validation_empty_recipient_list(client):
    payload = {
        "title": "Aereo Cloud Course",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_email_isolated_in_job(client):
    payload = {
        "title": "Aereo Cloud Course",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "not-a-valid-email"}
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    # Zero-drop fault isolation: request is accepted and error is isolated per-record
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["failed"] == 1
    assert any("email" in f["error"].lower() for f in data["failures"])


def test_validation_whitespace_name_isolated_in_job(client):
    payload = {
        "title": "Aereo Cloud Course",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "   ", "email": "valid@example.com"}
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    # Zero-drop fault isolation: request is accepted and error is isolated per-record
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["failed"] == 1
    assert any("name cannot be empty" in f["error"].lower() for f in data["failures"])


def test_validation_missing_title(client):
    payload = {
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"}
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_non_csv_upload(client):
    files = {"file": ("document.txt", b"plain text", "text/plain")}
    data = {
        "title": "Course",
        "issuer_name": "Aereo",
        "issue_date": "2026-10-07",
    }
    response = client.post("/api/v1/jobs/upload-csv", data=data, files=files)
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_validation_csv_missing_email_column(client):
    csv_content = "name,phone\nAlice,1234567890\n"
    files = {"file": ("recipients.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {
        "title": "Course",
        "issuer_name": "Aereo",
        "issue_date": "2026-10-07",
    }
    response = client.post("/api/v1/jobs/upload-csv", data=data, files=files)
    assert response.status_code == 422
    assert "email" in response.json()["detail"].lower()
