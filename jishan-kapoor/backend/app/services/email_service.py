import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """
    Sends an email via SMTP using the MAIL_* settings from config/.env
    (Zoho SMTP by default). Never raises - returns True/False so callers
    can decide how to handle a failed send.
    """
    host = current_app.config.get("MAIL_SERVER")
    port = current_app.config.get("MAIL_PORT")
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = current_app.config.get("MAIL_USE_TLS", True)
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username

    if not all([host, port, username, password]):
        current_app.logger.error(
            "Email not sent to %s: SMTP is not configured (check .env MAIL_* values).",
            to_email,
        )
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to_email

    if text_body:
        message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(host, int(port), timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(sender, [to_email], message.as_string())
        return True
    except Exception as exc:  # noqa: BLE001 - log and report failure, never crash the request
        current_app.logger.error("Failed to send email to %s: %s", to_email, exc)
        return False
