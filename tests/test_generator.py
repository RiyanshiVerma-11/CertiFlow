from pathlib import Path
from app.services.certificate_generator import CertificateGenerator
from app.config import settings


def test_certificate_pdf_generation_integrity(tmp_path):
    output_file = tmp_path / "test_cert_01.pdf"

    generated_path = CertificateGenerator.generate_pdf(
        recipient_name="Riyanshi Sharma",
        event_title="Aereo Cloud Geospatial Intelligence",
        issuer_name="Aereo Academy",
        issue_date="2026-10-07",
        certificate_code="CERT-TEST-9999",
        custom_note="Rank 1 Distinction",
        output_path=output_file,
    )

    assert generated_path.exists()
    assert generated_path.stat().st_size > 1000

    # Read binary header: PDF files start with %PDF-
    with open(generated_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"


def test_certificate_generator_handles_extreme_names(tmp_path):
    long_name = "Dr. Bartholomew Alexander Montgomery-Fitzgerald III"
    output_file = tmp_path / "test_cert_long.pdf"

    generated_path = CertificateGenerator.generate_pdf(
        recipient_name=long_name,
        event_title="Advanced Aerodynamics & Sensor Analytics",
        issuer_name="Aereo Academy",
        issue_date="2026-10-07",
        certificate_code="CERT-TEST-LONG",
        output_path=output_file,
    )

    assert generated_path.exists()
    assert generated_path.stat().st_size > 1000
