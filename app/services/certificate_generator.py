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
    def _draw_wrapped_centered_text(
        cls,
        c: canvas.Canvas,
        text: str,
        x_center: float,
        y_start: float,
        max_width: float,
        font_name: str,
        font_size: float,
        line_spacing: float,
        text_color,
        max_lines: int = 3,
    ) -> float:
        """
        Splits text into words and wraps across lines if it exceeds max_width.
        Draws each line centered at x_center, stepping down by line_spacing.
        """
        c.setFont(font_name, font_size)
        c.setFillColor(text_color)
        words = text.split()
        if not words:
            return y_start

        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            w = c.stringWidth(test_line, font_name, font_size)
            if w <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1] + "..."

        curr_y = y_start
        for line in lines:
            c.drawCentredString(x_center, curr_y, line)
            curr_y -= line_spacing

        return curr_y

    @classmethod
    def _format_issuer_lines(
        cls,
        c,
        text: str,
        font_name: str = "Helvetica-Bold",
        font_size: float = 8.5,
        max_width: float = 180.0,
    ) -> list[str]:
        """
        Splits an issuer/organization name into balanced lines.
        If the name fits within max_width, returns a single-item list.
        Otherwise, writes line 1 and line 2 (e.g., 'AEREO Directorate of Flight Operations'
        on line 1, and '& Aerial Systems' on line 2).
        Prioritizes natural conjunction breaks like ' & ' or ' and '.
        """
        text = text.strip()
        if not text:
            return []

        # If it already fits safely on a single line inside the border
        if c.stringWidth(text, font_name, font_size) <= max_width:
            return [text]

        # Prioritize natural conjunction break like " & "
        if " & " in text:
            parts = text.split(" & ", 1)
            l1, l2 = parts[0].strip(), f"& {parts[1].strip()}"
            if c.stringWidth(l1, font_name, font_size) <= max_width and c.stringWidth(l2, font_name, font_size) <= max_width:
                return [l1, l2]

        if " and " in text.lower():
            idx = text.lower().find(" and ")
            l1 = text[:idx].strip()
            l2 = text[idx:].strip()
            if c.stringWidth(l1, font_name, font_size) <= max_width and c.stringWidth(l2, font_name, font_size) <= max_width:
                return [l1, l2]

        words = text.split()
        if len(words) <= 1:
            return [text]

        # Find best split point so that neither line exceeds max_width
        mid = len(words) // 2
        best_lines = None
        best_score = float("inf")

        for split_at in range(1, len(words)):
            l1 = " ".join(words[:split_at])
            l2 = " ".join(words[split_at:])
            w1 = c.stringWidth(l1, font_name, font_size)
            w2 = c.stringWidth(l2, font_name, font_size)

            if w1 <= max_width and w2 <= max_width:
                score = abs(w1 - w2) + abs(split_at - mid) * 15
                if score < best_score:
                    best_score = score
                    best_lines = [l1, l2]

        if best_lines:
            return best_lines

        # Fallback greedy word-wrap if an unusually long string exceeds 2 lines
        lines = []
        curr = []
        for w in words:
            test = " ".join(curr + [w])
            if c.stringWidth(test, font_name, font_size) <= max_width or not curr:
                curr.append(w)
            else:
                lines.append(" ".join(curr))
                curr = [w]
        if curr:
            lines.append(" ".join(curr))
        return lines[:3]

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

        # 1. Background Fill (Subtle warm executive ivory)
        c.setFillColor(colors.HexColor("#faf9f6"))
        c.rect(0, 0, width, height, stroke=0, fill=1)

        # 2. Outer Border (Deep Slate Navy)
        c.setStrokeColor(cls.COLOR_PRIMARY)
        c.setLineWidth(4.5)
        c.rect(24, 24, width - 48, height - 48, stroke=1, fill=0)

        # 3. Inner Decorative Border (Rich Gold)
        c.setStrokeColor(cls.COLOR_GOLD)
        c.setLineWidth(1.5)
        c.rect(32, 32, width - 64, height - 64, stroke=1, fill=0)

        # 4. Corner Geometric Accents (Modern aerospace aesthetic)
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
        c.drawCentredString(width / 2, 392, recipient_name)

        # Name Underline flourish
        name_width = min(max(len(recipient_name) * 14, 200), width - 220)
        c.setStrokeColor(cls.COLOR_GOLD)
        c.setLineWidth(2)
        c.line((width - name_width) / 2, 376, (width + name_width) / 2, 376)

        # 7. Context / Reason Description
        c.setFillColor(cls.COLOR_SECONDARY)
        c.setFont("Helvetica", 13)
        c.drawCentredString(
            width / 2,
            324,
            "for successfully completing the curriculum and demonstrating proficiency in",
        )

        # 8. Event / Course Title (Wrapped safely within margins)
        title_y = 282 if custom_note else 272
        title_w = c.stringWidth(event_title, "Helvetica-Bold", 19)
        if title_w > (width - 180):
            # Auto-wrap long titles
            cls._draw_wrapped_centered_text(
                c=c,
                text=event_title,
                x_center=width / 2,
                y_start=title_y,
                max_width=width - 200,
                font_name="Helvetica-Bold",
                font_size=17,
                line_spacing=22,
                text_color=cls.COLOR_ACCENT,
                max_lines=2,
            )
        else:
            c.setFillColor(cls.COLOR_ACCENT)
            c.setFont("Helvetica-Bold", 19)
            c.drawCentredString(width / 2, title_y, event_title)

        # 9. Optional Custom Note / Honors Distinction Badge
        if custom_note:
            pill_text = f"★  {custom_note}  ★"
            c.setFont("Helvetica-Bold", 10.5)
            text_w = c.stringWidth(pill_text, "Helvetica-Bold", 10.5)
            pill_w = text_w + 32
            pill_h = 22
            pill_x = (width - pill_w) / 2
            pill_y = 228
            # Executive gold-tinted honors badge
            c.setFillColor(cls.COLOR_GOLD_LIGHT)
            c.setStrokeColor(cls.COLOR_GOLD)
            c.setLineWidth(1)
            c.roundRect(pill_x, pill_y, pill_w, pill_h, 5, fill=1, stroke=1)
            c.setFillColor(colors.HexColor("#b45309"))
            c.drawCentredString(width / 2, pill_y + 6, pill_text)

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
        sig_center_x = width - 155
        sig_half_w = 68

        # Stylized signature flourish above the line
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(cls.COLOR_PRIMARY)
        c.drawCentredString(sig_center_x, 134, "Dr. Vipul Sharma")

        # Signature horizontal line
        c.setStrokeColor(cls.COLOR_PRIMARY)
        c.setLineWidth(1)
        c.line(sig_center_x - sig_half_w, 122, sig_center_x + sig_half_w, 122)

        # Issuer / Organization Name — Balanced across 2 lines (half on line 1, remainder on line 2)
        issuer_lines = cls._format_issuer_lines(
            c=c,
            text=issuer_name,
            font_name="Helvetica-Bold",
            font_size=8.5,
            max_width=180.0,
        )

        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(cls.COLOR_PRIMARY)

        if len(issuer_lines) <= 1:
            line_text = issuer_lines[0] if issuer_lines else issuer_name
            c.drawCentredString(sig_center_x, 108, line_text)
            c.setFont("Helvetica", 8)
            c.setFillColor(cls.COLOR_MUTED)
            c.drawCentredString(sig_center_x, 92, "Authorized Signatory")
        elif len(issuer_lines) == 2:
            # First line (e.g., AEREO Directorate of Flight Operations)
            c.drawCentredString(sig_center_x, 108, issuer_lines[0])
            # Second line below it (e.g., & Aerial Systems)
            c.drawCentredString(sig_center_x, 96, issuer_lines[1])
            c.setFont("Helvetica", 8)
            c.setFillColor(cls.COLOR_MUTED)
            c.drawCentredString(sig_center_x, 82, "Authorized Signatory")
        else:
            c.drawCentredString(sig_center_x, 110, issuer_lines[0])
            c.drawCentredString(sig_center_x, 98, issuer_lines[1])
            c.drawCentredString(sig_center_x, 86, issuer_lines[2])
            c.setFont("Helvetica", 7.5)
            c.setFillColor(cls.COLOR_MUTED)
            c.drawCentredString(sig_center_x, 72, "Authorized Signatory")

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
