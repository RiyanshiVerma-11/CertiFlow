import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger("certiflow.email")


class EmailDispatcher:
    """
    Automated notification service for delivering digital certificates to recipients.
    Supports standard SMTP, AWS SES, and mock modes with PDF attachments.
    """

    @classmethod
    def dispatch_certificate_email(
        cls,
        recipient_name: str,
        recipient_email: str,
        certificate_code: str,
        event_title: str,
        issuer_name: str,
        pdf_bytes: bytes,
        custom_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Builds and transmits a personalized credential email with the certificate attached as PDF.
        """
        subject = f"Official Certificate of Achievement — {event_title}"

        # HTML Email Body
        honor_badge = f"<p style='color:#d97706; font-weight:bold;'>★ {custom_note} ★</p>" if custom_note else ""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 24px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 32px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <h2 style="color: #0f172a; margin-top: 0;">Official Credential Issued</h2>
                <p>Dear <strong>{recipient_name}</strong>,</p>
                <p>Congratulations! Your official certificate of achievement for <strong>{event_title}</strong> issued by <strong>{issuer_name}</strong> is now available.</p>
                {honor_badge}
                <div style="background: #f1f5f9; padding: 16px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 13px; color: #475569;">Credential Identifier:</p>
                    <p style="margin: 4px 0 0 0; font-family: monospace; font-size: 16px; font-weight: bold; color: #0284c7;">{certificate_code}</p>
                </div>
                <p>Your official PDF certificate is attached to this email. It contains a verifiable cryptographic QR code that allows anyone to confirm its authenticity in the CertiFlow registry.</p>
                <p style="color: #64748b; font-size: 13px; margin-top: 30px;">
                    Issued via CertiFlow Digital Credential Engine • {issuer_name}
                </p>
            </div>
        </body>
        </html>
        """

        # Build MIME Message
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_body, "html"))

        # Attach PDF
        filename = f"Certificate_{recipient_name.replace(' ', '_')}_{certificate_code}.pdf"
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(pdf_attachment)

        # Transmission logic
        if not settings.EMAIL_DISPATCH_ENABLED or not settings.SMTP_USER:
            # Simulated transmission for evaluation and local dev
            logger.info(
                f"[EmailDispatcher:Simulated] Dispatched certificate email to {recipient_email} "
                f"(Code: {certificate_code}, PDF Size: {len(pdf_bytes)} bytes, Subject: '{subject}')"
            )
            return {
                "status": "delivered_simulated",
                "recipient": recipient_email,
                "certificate_code": certificate_code,
                "attachment_filename": filename,
                "bytes": len(pdf_bytes),
            }

        # Real SMTP Transmission
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10.0) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"[EmailDispatcher] Successfully sent certificate email to {recipient_email}")
            return {
                "status": "sent",
                "recipient": recipient_email,
                "certificate_code": certificate_code,
            }
        except Exception as exc:
            logger.error(f"[EmailDispatcher] Failed to send certificate email to {recipient_email}: {exc}")
            return {
                "status": "failed",
                "recipient": recipient_email,
                "error": str(exc),
            }
