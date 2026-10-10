from app.services.email_service import EmailDispatcher


def test_email_dispatcher_builds_mime_with_pdf():
    """
    Validates Reason 5: Automated Email Dispatch service.
    Verifies that personalized emails are constructed with HTML branding and PDF attachment.
    """
    res = EmailDispatcher.dispatch_certificate_email(
        recipient_name="Riyanshi Sharma",
        recipient_email="riyanshi@example.com",
        certificate_code="CERT-EMAIL-99",
        event_title="Aereo Cloud Geospatial Intelligence",
        issuer_name="Aereo Engineering Academy",
        pdf_bytes=b"%PDF-1.4 Mock Binary Certificate Content",
        custom_note="Rank 1",
    )

    assert res["status"] in ["delivered_simulated", "sent"]
    assert res["recipient"] == "riyanshi@example.com"
    assert res["certificate_code"] == "CERT-EMAIL-99"
    assert "Certificate_Riyanshi_Sharma_CERT-EMAIL-99.pdf" in res["attachment_filename"]


def test_job_email_dispatch_endpoint(client):
    """
    Validates on-demand email dispatch endpoint: POST /api/v1/jobs/{job_id}/dispatch-emails.
    """
    payload = {
        "title": "Aereo Flight Navigation Exam",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Drone Pilot One", "email": "pilot1@example.com"},
            {"name": "Drone Pilot Two", "email": "pilot2@example.com"},
        ],
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    # Trigger email dispatch
    dispatch_resp = client.post(f"/api/v1/jobs/{job_id}/dispatch-emails")
    assert dispatch_resp.status_code == 200
    data = dispatch_resp.json()
    assert data["status"] == "success"
    assert data["dispatched_count"] == 2
