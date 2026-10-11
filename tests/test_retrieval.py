import io
import zipfile
from app.services.job_service import JobService


def test_certificate_download_and_bulk_zip(client):
    payload = {
        "title": "Aereo Cloud Certification",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Riyanshi Verma", "email": "riyanshi@example.com"},
            {"name": "Alex Mercer", "email": "alex@example.com"},
        ],
    }

    # 1. Create job (TestClient executes BackgroundTasks upon request completion)
    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    # 2. Retrieve list of certificates
    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    certs_data = certs_resp.json()
    assert "items" in certs_data
    assert certs_data["total"] == 2
    certs = certs_data["items"]
    assert len(certs) == 2

    first_cert = certs[0]
    cert_id = first_cert["id"]
    cert_code = first_cert["certificate_code"]

    # 4. Download individual certificate PDF
    dl_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert dl_resp.content.startswith(b"%PDF-")

    # 5. Download bulk ZIP archive
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"

    # Verify that the zip contains both generated PDFs
    zip_buffer = io.BytesIO(zip_resp.content)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        assert all(n.endswith(".pdf") for n in namelist)

    # 6. Verify certificate authenticity endpoint
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_valid"] is True
    assert verify_data["recipient_name"] == first_cert["recipient_name"]
    assert verify_data["certificate_code"] == cert_code

    # 7. Test invalid certificate code lookup
    bad_verify_resp = client.get("/api/v1/certificates/verify/NON-EXISTENT-CODE")
    assert bad_verify_resp.status_code == 200
    assert bad_verify_resp.json()["is_valid"] is False
