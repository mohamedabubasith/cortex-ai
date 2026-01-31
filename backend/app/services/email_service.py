import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME

    def send_email(self, email_to: str, subject: str, html_content: str):
        provider = settings.EMAIL_PROVIDER.lower()

        if provider == "none":
            logger.info("Email provider is set to 'none'. Skipping email.")
            return

        if provider == "console":
            logger.info("="*50)
            logger.info(f"EMAIL TO: {email_to}")
            logger.info(f"SUBJECT: {subject}")
            logger.info("CONTENT:")
            logger.info(html_content)
            logger.info("="*50)
            return

        # Default to SMTP
        if not self.smtp_host or not self.smtp_user:
            logger.warning("SMTP settings not configured but provider is 'smtp'. Email not sent.")
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = email_to

        part = MIMEText(html_content, "html")
        message.attach(part)

        # Helper function to attempt sending
        def attempt_send(port_to_try):
            try:
                logger.info(f"Attempting to send email via {self.smtp_host}:{port_to_try}...")
                print(f"Attempting to send email via {self.smtp_host}:{port_to_try}...")
                
                if port_to_try == 465:
                    with smtplib.SMTP_SSL(self.smtp_host, port_to_try, timeout=15) as server:
                        server.login(self.smtp_user, self.smtp_password)
                        server.sendmail(self.from_email, email_to, message.as_string())
                else:
                    with smtplib.SMTP(self.smtp_host, port_to_try, timeout=15) as server:
                        if self.smtp_tls or port_to_try == 587:
                            server.starttls()
                        server.login(self.smtp_user, self.smtp_password)
                        server.sendmail(self.from_email, email_to, message.as_string())
                return True, None
            except Exception as e:
                return False, str(e)

        # 1. Try Configured Port first
        success, error = attempt_send(self.smtp_port)
        if success:
            logger.info(f"✅ EMAIL SENT SUCCESSFULLY to {email_to} on port {self.smtp_port}")
            print(f"✅ EMAIL SENT SUCCESSFULLY to {email_to} on port {self.smtp_port}")
            return

        # 2. Setup Fallback Port
        fallback_port = 587 if self.smtp_port == 465 else 465
        logger.warning(f"⚠️ Port {self.smtp_port} failed ({error}). Retrying with fallback port {fallback_port}...")
        print(f"⚠️ Port {self.smtp_port} failed. Retrying with fallback port {fallback_port}...")

        # 3. Try Fallback Port
        success_fallback, error_fallback = attempt_send(fallback_port)
        if success_fallback:
            logger.info(f"✅ EMAIL SENT SUCCESSFULLY to {email_to} on fallback port {fallback_port}")
            print(f"✅ EMAIL SENT SUCCESSFULLY to {email_to} on fallback port {fallback_port}")
        else:
            logger.error(f"❌ FAILED to send email on both ports. Primary: {error}, Fallback: {error_fallback}")
            print(f"❌ FAILED to send email on both ports. Primary: {error}, Fallback: {error_fallback}")

    def send_reset_password_email(self, email_to: str, token: str):
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Password Recovery"
        
        # Use configured frontend URL
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body>
                <h1>Password Recovery</h1>
                <p>You requested a password recovery for your account.</p>
                <p>Please click the link below to reset your password:</p>
                <a href="{reset_link}">Reset Password</a>
                <p>If you didn't request this, please ignore this email.</p>
                <p>This link will expire in {settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.</p>
            </body>
        </html>
        """
        self.send_email(email_to, subject, html_content)
