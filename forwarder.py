"""
forwarder.py
=============
Core SMS-to-Email Forwarding Engine.
Handles SMTP connections (SSL & TLS), email formatting, multi-recipient delivery,
and persistent configuration storage.
"""

import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SMSForwarder")

CONFIG_FILE = "sms_forwarder_config.json"


class SMSForwarder:
    """Manages SMTP settings and forwards SMS messages to email addresses."""

    DEFAULT_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_ssl": False,  # True for port 465 (SSL), False for 587 (STARTTLS)
        "sender_email": "",
        "sender_password": "",  # App Password (e.g. for Gmail/Outlook)
        "recipient_emails": [],  # List of destination emails
        "subject_prefix": "[SMS Forwarded]",
        "device_name": "My Mobile",
        "is_active": True,
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict = self.load_config()

    def _get_default_config_path(self) -> str:
        """Determines writable directory for config (works on Desktop and Android)."""
        # In Android, kivy provides app storage; fallback to local dir
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app and hasattr(app, "user_data_dir"):
                return os.path.join(app.user_data_dir, CONFIG_FILE)
        except Exception:
            pass
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)

    def load_config(self) -> Dict:
        """Loads configuration from JSON file or initializes default."""
        config = self.DEFAULT_CONFIG.copy()
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    config.update(saved)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        return config

    def save_config(self, new_config: Optional[Dict] = None) -> bool:
        """Persists current configuration to JSON file."""
        if new_config:
            self.config.update(new_config)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def get_recipients_list(self) -> List[str]:
        """Returns clean list of recipient emails."""
        raw = self.config.get("recipient_emails", [])
        if isinstance(raw, str):
            # Split comma or semicolon separated string
            parts = [e.strip() for e in raw.replace(";", ",").split(",") if e.strip()]
            return parts
        elif isinstance(raw, list):
            return [str(e).strip() for e in raw if str(e).strip()]
        return []

    def test_connection(self) -> Tuple[bool, str]:
        """
        Tests the SMTP connection and credentials without sending a message.
        Returns (success: bool, message: str).
        """
        smtp_server = self.config.get("smtp_server", "").strip()
        smtp_port = int(self.config.get("smtp_port", 587))
        use_ssl = bool(self.config.get("use_ssl", False))
        sender_email = self.config.get("sender_email", "").strip()
        sender_password = self.config.get("sender_password", "").strip()

        if not smtp_server or not sender_email or not sender_password:
            return False, "Missing SMTP server, sender email, or password."

        try:
            if use_ssl or smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(sender_email, sender_password)
            server.quit()
            return True, "SMTP connection and login succeeded!"
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return False, f"Authentication error: {e.smtp_error.decode('utf-8', errors='ignore') if hasattr(e, 'smtp_error') else str(e)}. Check your App Password."
        except Exception as e:
            logger.error(f"SMTP connection error: {e}")
            return False, f"Connection failed: {str(e)}"

    def send_test_email(self) -> Tuple[bool, str]:
        """Sends a verification email to all configured recipients."""
        recipients = self.get_recipients_list()
        if not recipients:
            return False, "No recipient email addresses configured."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"{self.config.get('subject_prefix', '[SMS Forwarder]')} Test Email"
        body = (
            "Congratulations!\n\n"
            "Your SMS Forwarder email settings are configured properly.\n"
            f"Timestamp: {timestamp}\n"
            f"Device: {self.config.get('device_name', 'Mobile Device')}\n\n"
            "Incoming SMS messages will be forwarded automatically to this email."
        )
        return self._send_email_raw(subject=subject, body_text=body, recipients=recipients, sender_label="SMS Forwarder Test")

    def forward_sms(
        self,
        sender_number: str,
        message_body: str,
        received_timestamp: Optional[str] = None,
        sim_slot: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Main function to forward an incoming SMS to recipient email(s).

        :param sender_number: Phone number or sender ID (e.g., '+1234567890' or 'BANKOTP')
        :param message_body: Raw text content of the SMS message
        :param received_timestamp: Optional string timestamp (defaults to current time)
        :param sim_slot: Optional SIM card indicator (e.g. 'SIM 1')
        :return: (success: bool, status_message: str)
        """
        if not self.config.get("is_active", True):
            logger.info("Forwarder is paused; skipping SMS forwarding.")
            return False, "Forwarder service is currently paused in settings."

        recipients = self.get_recipients_list()
        if not recipients:
            logger.warning("No recipient emails configured; cannot forward SMS.")
            return False, "No recipient emails configured."

        if not received_timestamp:
            received_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prefix = self.config.get("subject_prefix", "[SMS Forwarded]").strip()
        device = self.config.get("device_name", "Mobile Device")
        sim_info = f" ({sim_slot})" if sim_slot else ""

        # Subject format: [SMS Forwarded] From: +1234567890
        subject = f"{prefix} From: {sender_number}"

        # Plain text version
        body_text = (
            f"--- INCOMING SMS FORWARDED ---\n"
            f"From: {sender_number}\n"
            f"Received: {received_timestamp}\n"
            f"Device: {device}{sim_info}\n"
            f"------------------------------\n\n"
            f"{message_body}\n\n"
            f"------------------------------\n"
            f"Auto-forwarded by Mobile Message Forwarder"
        )

        # HTML formatted version for clean viewing
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #1e293b; }}
                .card {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }}
                .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; padding: 20px 24px; }}
                .header h2 {{ margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.5px; }}
                .header p {{ margin: 4px 0 0 0; font-size: 13px; opacity: 0.85; }}
                .meta-table {{ width: 100%; border-collapse: collapse; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
                .meta-table td {{ padding: 10px 24px; font-size: 13px; }}
                .meta-label {{ color: #64748b; font-weight: 600; width: 110px; }}
                .meta-val {{ color: #0f172a; font-weight: 500; }}
                .content-box {{ padding: 24px; background: #ffffff; }}
                .sms-message {{ background: #f1f5f9; border-left: 4px solid #2563eb; padding: 16px 20px; border-radius: 6px; font-size: 16px; line-height: 1.6; color: #0f172a; word-break: break-word; white-space: pre-wrap; }}
                .footer {{ padding: 14px 24px; background: #f8fafc; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h2>Incoming SMS Message</h2>
                    <p>Forwarded automatically from your mobile device</p>
                </div>
                <table class="meta-table">
                    <tr>
                        <td class="meta-label">From:</td>
                        <td class="meta-val"><strong>{sender_number}</strong></td>
                    </tr>
                    <tr>
                        <td class="meta-label">Date & Time:</td>
                        <td class="meta-val">{received_timestamp}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Device:</td>
                        <td class="meta-val">{device}{sim_info}</td>
                    </tr>
                </table>
                <div class="content-box">
                    <div class="sms-message">{message_body}</div>
                </div>
                <div class="footer">
                    Sent via Mobile SMS Forwarder (Python Android Edition)
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email_raw(
            subject=subject,
            body_text=body_text,
            recipients=recipients,
            body_html=body_html,
            sender_label=f"SMS: {sender_number}"
        )

    def _send_email_raw(
        self,
        subject: str,
        body_text: str,
        recipients: List[str],
        body_html: Optional[str] = None,
        sender_label: str = "SMS Forwarder"
    ) -> Tuple[bool, str]:
        """Internal helper to dispatch email via SMTP."""
        smtp_server = self.config.get("smtp_server", "").strip()
        smtp_port = int(self.config.get("smtp_port", 587))
        use_ssl = bool(self.config.get("use_ssl", False))
        sender_email = self.config.get("sender_email", "").strip()
        sender_password = self.config.get("sender_password", "").strip()

        if not smtp_server or not sender_email or not sender_password:
            return False, "SMTP configuration incomplete (server, email, or password missing)."

        if not recipients:
            return False, "No recipient emails provided."

        try:
            # Build MIME Message with full RFC-compliant headers
            from email.header import Header
            from email.utils import formataddr, formatdate, make_msgid

            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = formataddr((str(Header(sender_label, "utf-8")), sender_email))
            msg["To"] = ", ".join(recipients)
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain=sender_email.split("@")[-1] if "@" in sender_email else "gmail.com")
            msg["MIME-Version"] = "1.0"
            msg["X-Mailer"] = "Mobile-SMS-Forwarder"

            # Attach plain text
            part1 = MIMEText(body_text, "plain", "utf-8")
            msg.attach(part1)

            # Attach HTML if provided
            if body_html:
                part2 = MIMEText(body_html, "html", "utf-8")
                msg.attach(part2)

            # Connect
            if use_ssl or smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
            server.quit()

            recipients_str = ", ".join(recipients)
            logger.info(f"Successfully forwarded message to: {recipients_str}")
            return True, f"Forwarded to: {recipients_str}"

        except smtplib.SMTPAuthenticationError as e:
            err = f"SMTP Authentication failed: {e.smtp_error.decode('utf-8', errors='ignore') if hasattr(e, 'smtp_error') else str(e)}"
            logger.error(err)
            return False, err
        except Exception as e:
            err = f"Failed to send email: {str(e)}"
            logger.error(err)
            return False, err
