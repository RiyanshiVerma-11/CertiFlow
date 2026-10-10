import io
from pathlib import Path
from typing import Optional
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from app.config import settings
from app.services.storage_service import get_storage_provider


class CertificateGenerator:
    """Executive-grade vector PDF certificate generator using ReportLab."""

    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)  # 841.89 x 595.27 points

    # Curated palette
    COLOR_PRIMARY = colors.HexColor("#0f172a")      # Slate 900
    COLOR_SECONDARY = colors.HexColor("#1e293b")    # Slate 800
    COLOR_ACCENT = colors.HexColor("#0284c7")       # Sky 600
    COLOR_GOLD = colors.HexColor("#d97706")         # Amber / Gold 600
    COLOR_GOLD_LIGHT = colors.HexColor("#fef3c7")   # Gold 100
    COLOR_MUTED = colors.HexColor("#64748b")        # Slate 500
    COLOR_BORDER = colors.HexColor("#cbd5e1")       # Slate 300

    @classmethod
    def generate_pdf_bytes(
        cls,
        recipient_name: str,
        event_title: str,
        issuer_name: str,
        issue_date: str,
        certificate_code: str,
        recipient_id: Optional[str] = None,
        custom_note: Optional[str] = None,
    ) -> bytes:
        """
        Renders a certificate directly into an in-memory byte stream without disk I/O.
        """
        buf = io.BytesIO()
        cls._render_canvas(
            buf,
            recipient_name=recipient_name,
            event_title=event_title,
            issuer_name=issuer_name,
            issue_date=issue_date,
            certificate_code=certificate_code,
            recipient_id=recipient_id,
            custom_note=custom_note,
        )
        return buf.getvalue()

    @classmethod
    def generate_pdf(
        cls,
        recipient_name: str,
        event_title: str,
        issuer_name: str,
        issue_date: str,
        certificate_code: str,
        recipient_id: Optional[str] = None,
        custom_note: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Renders a high-resolution, vector-sharp PDF certificate.
        Persists using the configured StorageProvider abstraction or output_path.
        Returns the Path to the generated PDF.
        """
        storage = get_storage_provider()

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cls._render_canvas(
                str(output_path),
                recipient_name=recipient_name,
                event_title=event_title,
                issuer_name=issuer_name,
                issue_date=issue_date,
                certificate_code=certificate_code,
                recipient_id=recipient_id,
                custom_note=custom_note,
            )
            return output_path

        # Generate in memory and persist via StorageProvider
        pdf_bytes = cls.generate_pdf_bytes(
            recipient_name=recipient_name,
            event_title=event_title,
            issuer_name=issuer_name,
            issue_date=issue_date,
            certificate_code=certificate_code,
            recipient_id=recipient_id,
            custom_note=custom_note,
        )
        storage_key = storage.save_certificate(certificate_code, pdf_bytes)
        local_path = storage.get_local_path(storage_key)
        return local_path if local_path is not None else Path(storage_key)

    @classmethod
    def _render_canvas(
        cls,
        target,
        recipient_name: str,
        event_title: str,
        issuer_name: str,
        issue_date: str,
        certificate_code: str,
        recipient_id: Optional[str] = None,
        custom_note: Optional[str] = None,
    ):
        c = canvas.Canvas(target, pagesize=landscape(A4))
        width, height = cls.PAGE_WIDTH, cls.PAGE_HEIGHT

        # 1. Background Fill
        c.setFillColor(colors.HexColor("#fafafa"))
        c.rect(0, 0, width, height, stroke=0, fill=1)

        # 2. Outer Border (Deep Slate)
        c.setStrokeColor(cls.COLOR_PRIMARY)
        c.setLineWidth(5)
        c.rect(24, 24, width - 48, height - 48, stroke=1, fill=0)

        # 3. Inner Decorative Border (Gold)
        c.setStrokeColor(cls.COLOR_GOLD)
        c.setLineWidth(1.5)
        c.rect(32, 32, width - 64, height - 64, stroke=1, fill=0)

        # 4. Corner Geometric Accents (Modern tech aesthetic)
        corner_size = 20
        c.setStrokeColor(cls.COLOR_GOLD)
        c.setLineWidth(2)
        # Top-left corner
        c.line(28, height - 28 - corner_size, 28, height - 28)
        c.line(28, height - 28, 28 + corner_size, height - 28)
        # Top-right corner
        c.line(width - 28 - corner_size, height - 28, width - 28, height - 28)
        c.line(width - 28, height - 28, width - 28, height - 28 - corner_size)
        # Bottom-left corner
        c.line(28, 28 + corner_size, 28, 28)
        c.line(28, 28, 28 + corner_size, 28)
        # Bottom-right corner
        c.line(width - 28 - corner_size, 28, width - 28, 28)
        c.line(width - 28, 28, width - 28, 28 + corner_size)

        # 5. Top Header Banner & Seal
        c.setFillColor(cls.COLOR_GOLD)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width / 2, 532, "OFFICIAL CREDENTIAL • VERIFIED RECORD")

        c.setFillColor(cls.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width / 2, 492, "CERTIFICATE OF ACHIEVEMENT")

        c.setFillColor(cls.COLOR_MUTED)
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, 454, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

        # 6. Recipient Name (Dynamic font scaling for long names)
        name_font_size = 32
        if len(recipient_name) > 30:
            name_font_size = 22
        elif len(recipient_name) > 22:
            name_font_size = 26

        c.setFillColor(cls.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", name_font_size)
        c.drawCentredString(width / 2, 388, recipient_name)

        # Name Underline flourish
        name_width = min(max(len(recipient_name) * 14, 200), width - 200)
        c.setStrokeColor(cls.COLOR_GOLD)
        c.setLineWidth(2)
        c.line((width - name_width) / 2, 374, (width + name_width) / 2, 374)

        # 7. Context / Reason Description
        c.setFillColor(cls.COLOR_SECONDARY)
        c.setFont("Helvetica", 13)
        c.drawCentredString(
            width / 2,
            322,
            "for successfully completing the curriculum and demonstrating proficiency in",
        )

        # 8. Event / Course Title
        c.setFillColor(cls.COLOR_ACCENT)
        c.setFont("Helvetica-Bold", 19)
        title_y = 280 if custom_note else 268
        c.drawCentredString(width / 2, title_y, event_title)

        # 9. Optional Custom Note / Honors Distinction Badge
        if custom_note:
            pill_text = f"★  {custom_note}  ★"
            c.setFont("Helvetica-Bold", 11)
            text_w = c.stringWidth(pill_text, "Helvetica-Bold", 11)
            pill_w = text_w + 32
            pill_h = 24
            pill_x = (width - pill_w) / 2
            pill_y = 230
            # Executive gold-tinted honors badge
            c.setFillColor(cls.COLOR_GOLD_LIGHT)
            c.setStrokeColor(cls.COLOR_GOLD)
            c.setLineWidth(1)
            c.roundRect(pill_x, pill_y, pill_w, pill_h, 6, fill=1, stroke=1)
            c.setFillColor(colors.HexColor("#b45309"))
            c.drawCentredString(width / 2, pill_y + 7, pill_text)

        # 10. Divider Line
        c.setStrokeColor(cls.COLOR_BORDER)
        c.setLineWidth(0.8)
        c.line(80, 196, width - 80, 196)

        # 11. QR Code Generation for Instant Verification
        qr_reader = cls._generate_qr_code(certificate_code)
        c.drawImage(qr_reader, 75, 82, width=78, height=78)
        c.setFillColor(cls.COLOR_MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(75, 68, "Scan to Verify Authenticity")

        # 12. Center Metadata Block
        c.setFillColor(cls.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(width / 2, 146, "CREDENTIAL IDENTIFIER")
        c.setFillColor(cls.COLOR_ACCENT)
        c.setFont("Courier-Bold", 11)
        cred_text = certificate_code if not recipient_id else f"{certificate_code}  •  ID: {recipient_id}"
        c.drawCentredString(width / 2, 128, cred_text)

        c.setFillColor(cls.COLOR_MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(width / 2, 108, f"Issued Date: {issue_date}")
        c.drawCentredString(width / 2, 92, "Digitally signed and archived in the CertiFlow registry")

        # 13. Signature & Issuer Block (Bottom-Right)
        c.setStrokeColor(cls.COLOR_PRIMARY)
        c.setLineWidth(1)
        c.line(width - 240, 125, width - 70, 125)

        c.setFillColor(cls.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(width - 155, 108, issuer_name)

        c.setFillColor(cls.COLOR_MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(width - 155, 92, "Authorized Signatory")

        c.showPage()
        c.save()

    @staticmethod
    def _generate_qr_code(certificate_code: str):
        """Generates an in-memory QR code ImageReader linking to verification."""
        from reportlab.lib.utils import ImageReader
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1,
        )
        verify_data = f"CERTIFLOW:{certificate_code}"
        qr.add_data(verify_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="white")
        buf = io.BytesIO()
        if hasattr(img, "_img"):
            img._img.save(buf, format="PNG")
        else:
            img.save(buf)
        buf.seek(0)
        return ImageReader(buf)
