import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse

import requests
from flask import current_app


def _normalize_smtp_host(value: str | None) -> str:
    """Accept a hostname or pasted URL and return a hostname for smtplib."""
    host = str(value or "").strip()
    if not host:
        return ""
    if "://" in host:
        return urlparse(host).hostname or ""
    return host.split("/", 1)[0]


def _send_with_brevo(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    """Send email through Brevo's HTTPS API (works on Render Free)."""
    api_key = current_app.config.get("BREVO_API_KEY")
    api_url = current_app.config.get("BREVO_API_URL")
    sender_email = current_app.config.get("BREVO_SENDER_EMAIL")
    sender_name = current_app.config.get("BREVO_SENDER_NAME") or "Smart Society"

    if not all([api_key, api_url, sender_email]):
        return False

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if text_body:
        payload["textContent"] = text_body

    try:
        response = requests.post(
            api_url,
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if response.ok:
            current_app.logger.info(
                "Brevo accepted email delivery request for %s", to_email
            )
            return True

        current_app.logger.error(
            "Brevo rejected email for %s with HTTP %s: %s",
            to_email,
            response.status_code,
            response.text[:500],
        )
        return False
    except requests.RequestException as exc:
        current_app.logger.error(
            "Brevo email request failed for %s: %s", to_email, exc
        )
        return False


def _send_with_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    """SMTP fallback for local or paid hosting environments."""
    host = _normalize_smtp_host(current_app.config.get("MAIL_SERVER"))
    port = current_app.config.get("MAIL_PORT")
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    use_tls = current_app.config.get("MAIL_USE_TLS", True)
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username

    if not all([host, port, username, password]):
        current_app.logger.error(
            "Email delivery is not configured: set Brevo or SMTP variables."
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
    except Exception as exc:  # noqa: BLE001 - return a safe failure to the route
        current_app.logger.error("SMTP email failed for %s: %s", to_email, exc)
        return False


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """
    Send with Brevo over HTTPS when BREVO_API_KEY is configured. Fall back to
    SMTP only when Brevo is not configured. Never raises: callers receive a
    boolean and can avoid changing credentials when delivery fails.
    """
    if current_app.config.get("BREVO_API_KEY"):
        return _send_with_brevo(to_email, subject, html_body, text_body)
    return _send_with_smtp(to_email, subject, html_body, text_body)
