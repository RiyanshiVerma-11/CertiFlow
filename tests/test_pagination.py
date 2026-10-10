def test_certificate_pagination_limits_and_pages(client):
    """
    Validates Reason 7: limit/offset pagination on GET /jobs/{job_id}/certificates.
    Verifies that bulk retrieval is split into pages with proper metadata.
    """
    recipients = [
        {"name": f"Recipient {i:02d}", "email": f"user{i:02d}@example.com"}
        for i in range(1, 11)
    ]
    payload = {
        "title": "Aereo Enterprise Pagination Test",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": recipients,
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["job_id"]

    # 1. Fetch Page 1 with limit 4
    page1_resp = client.get(f"/api/v1/jobs/{job_id}/certificates?page=1&limit=4")
    assert page1_resp.status_code == 200
    p1 = page1_resp.json()
    assert p1["total"] == 10
    assert p1["page"] == 1
    assert p1["limit"] == 4
    assert p1["total_pages"] == 3
    assert p1["has_next"] is True
    assert p1["has_prev"] is False
    assert len(p1["items"]) == 4

    # 2. Fetch Page 2 with limit 4
    page2_resp = client.get(f"/api/v1/jobs/{job_id}/certificates?page=2&limit=4")
    assert page2_resp.status_code == 200
    p2 = page2_resp.json()
    assert p2["page"] == 2
    assert p2["has_next"] is True
    assert p2["has_prev"] is True
    assert len(p2["items"]) == 4
    # Ensure items on Page 2 are different from Page 1
    p1_ids = {item["id"] for item in p1["items"]}
    p2_ids = {item["id"] for item in p2["items"]}
    assert p1_ids.isdisjoint(p2_ids)

    # 3. Fetch Page 3 (last page with remaining 2 items)
    page3_resp = client.get(f"/api/v1/jobs/{job_id}/certificates?page=3&limit=4")
    assert page3_resp.status_code == 200
    p3 = page3_resp.json()
    assert p3["page"] == 3
    assert p3["has_next"] is False
    assert p3["has_prev"] is True
    assert len(p3["items"]) == 2


def test_certificate_pagination_status_filtering(client):
    """
    Validates filtering certificates by status (SUCCESS vs FAILED) within paginated query.
    """
    payload = {
        "title": "Aereo Filter Test",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Valid 1", "email": "valid1@example.com"},
            {"name": "Bad 1", "email": "broken-email@"},
            {"name": "Valid 2", "email": "valid2@example.com"},
        ],
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    # Filter only SUCCESS
    success_resp = client.get(f"/api/v1/jobs/{job_id}/certificates?status=SUCCESS")
    assert success_resp.status_code == 200
    s_data = success_resp.json()
    assert s_data["total"] == 2
    assert all(c["status"] == "SUCCESS" for c in s_data["items"])

    # Filter only FAILED
    failed_resp = client.get(f"/api/v1/jobs/{job_id}/certificates?status=FAILED")
    assert failed_resp.status_code == 200
    f_data = failed_resp.json()
    assert f_data["total"] == 1
    assert all(c["status"] == "FAILED" for c in f_data["items"])
