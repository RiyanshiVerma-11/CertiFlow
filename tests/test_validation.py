def test_validation_empty_recipient_list(client):
    payload = {
        "title": "Aereo Cloud Course",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_email(client):
    payload = {
        "title": "Aereo Cloud Course",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "not-a-valid-email"}
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("email" in str(e).lower() for e in errors)


def test_validation_whitespace_name(client):
    payload = {
        "title": "Aereo Cloud Course",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "   ", "email": "valid@example.com"}
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


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
