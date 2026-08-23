import io
import os
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "TestAdmin123!"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-longer-than-32-characters"
os.environ["JWT_SECRET_KEY"] = "test-jwt-key-that-is-longer-than-32-characters"
os.environ["SEED_DEMO_DATA"] = "true"

from app import create_app
from app.models import (
    Category,
    Complaint,
    ComplaintUpdate,
    Feedback,
    Notification,
    PasswordResetOtp,
    User,
)


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        yield application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


def _login(client, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    return {"Authorization": f"Bearer {response.json['access_token']}"}


def test_seed_is_realistic_and_idempotent(app):
    expected = {
        "users": 8,
        "categories": 7,
        "complaints": 6,
        "complaint_updates": 8,
        "feedbacks": 2,
        "notifications": 2,
    }
    models = [User, Category, Complaint, ComplaintUpdate, Feedback, Notification]
    assert {model.__tablename__: model.query.count() for model in models} == expected

    from app.seed import seed_demo_data

    seed_demo_data()
    assert {model.__tablename__: model.query.count() for model in models} == expected
    with patch.dict(
        os.environ,
        {"RECOVERY_TEST_EMAIL": "recovery.test@example.net"},
    ):
        seed_demo_data()
        assert User.query.filter_by(
            name="Emily Carter",
            email="recovery.test@example.net",
        ).first()
    seed_demo_data()
    assert User.query.filter_by(
        name="Emily Carter",
        email="emily.carter@example.com",
    ).first()
    assert Category.query.filter_by(name="Plumbing", is_active=True).first()
    assert Complaint.query.filter_by(title="Kitchen sink leak worsening").first()
    assert {
        user.name
        for user in User.query.filter(User.email != "admin@example.com").all()
    } == {
        "Amelia Parker",
        "Emma Collins",
        "Emily Carter",
        "Jack Thompson",
        "James Wilson",
        "Oliver Turner",
        "Sophie Bennett",
    }


def test_admin_password_rotates_from_environment(app, client):
    from app import _sync_admin_credentials

    rotated_email = "admin@society.com"
    rotated_password = "RotatedAdmin123!"
    with patch.dict(
        os.environ,
        {
            "ADMIN_EMAIL": rotated_email,
            "ADMIN_PASSWORD": rotated_password,
        },
    ):
        with app.app_context():
            _sync_admin_credentials()
        assert client.post(
            "/auth/login",
            json={"email": rotated_email, "password": rotated_password},
        ).status_code == 200
        assert client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "TestAdmin123!"},
        ).status_code == 401

    with app.app_context():
        _sync_admin_credentials()


def test_password_recovery_email_edge_cases(app, client):
    from app import _sync_admin_credentials

    invalid = client.post("/auth/forgot-password", json={"email": "not-an-email"})
    assert invalid.status_code == 400

    with patch("app.services.auth_service.send_email") as send_email:
        unknown = client.post(
            "/auth/forgot-password",
            json={"email": "missing@example.com"},
        )
        assert unknown.status_code == 200
        send_email.assert_not_called()

    with patch("app.services.auth_service.send_email", return_value=False):
        failed = client.post(
            "/auth/forgot-password",
            json={"email": "admin@example.com"},
        )
        assert failed.status_code == 502
        _login(client, "admin@example.com", "TestAdmin123!")
        with app.app_context():
            assert PasswordResetOtp.query.count() == 0

    malformed_verification = client.post(
        "/auth/verify-reset-otp",
        json={
            "email": "admin@example.com",
            "otp": "12345",
            "password": "weak",
        },
    )
    assert malformed_verification.status_code == 400

    delivered = {}

    def capture_email(to_email, subject, html_body, text_body):
        delivered.update(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        return True

    with patch("app.services.auth_service.send_email", side_effect=capture_email):
        accepted = client.post(
            "/auth/forgot-password",
            json={"email": "admin@example.com"},
        )
        assert accepted.status_code == 200

    assert delivered["to_email"] == "admin@example.com"
    assert "Verification Code" in delivered["subject"]
    otp = re.search(
        r"verification code is: (\d{6})",
        delivered["text_body"],
    ).group(1)
    _login(client, "admin@example.com", "TestAdmin123!")

    wrong_code = client.post(
        "/auth/verify-reset-otp",
        json={
            "email": "admin@example.com",
            "otp": "000000",
            "password": "RecoveredAdmin123!",
        },
    )
    assert wrong_code.status_code == 400
    _login(client, "admin@example.com", "TestAdmin123!")

    verified = client.post(
        "/auth/verify-reset-otp",
        json={
            "email": "admin@example.com",
            "otp": otp,
            "password": "RecoveredAdmin123!",
        },
    )
    assert verified.status_code == 200
    assert client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "TestAdmin123!"},
    ).status_code == 401
    _login(client, "admin@example.com", "RecoveredAdmin123!")
    assert client.post(
        "/auth/verify-reset-otp",
        json={
            "email": "admin@example.com",
            "otp": otp,
            "password": "AnotherAdmin123!",
        },
    ).status_code == 400

    with app.app_context():
        _sync_admin_credentials()

    delivered.clear()
    with patch("app.services.auth_service.send_email", side_effect=capture_email):
        assert client.post(
            "/auth/forgot-password",
            json={"email": "admin@example.com"},
        ).status_code == 200
    expired_otp = re.search(
        r"verification code is: (\d{6})",
        delivered["text_body"],
    ).group(1)
    with app.app_context():
        reset = PasswordResetOtp.query.one()
        reset.expires_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(seconds=1)
        )
        from app.extensions import db

        db.session.commit()
    assert client.post(
        "/auth/verify-reset-otp",
        json={
            "email": "admin@example.com",
            "otp": expired_otp,
            "password": "ExpiredAdmin123!",
        },
    ).status_code == 400
    _login(client, "admin@example.com", "TestAdmin123!")

    delivered.clear()
    with patch("app.services.auth_service.send_email", side_effect=capture_email):
        assert client.post(
            "/auth/forgot-password",
            json={"email": "admin@example.com"},
        ).status_code == 200
    locked_otp = re.search(
        r"verification code is: (\d{6})",
        delivered["text_body"],
    ).group(1)
    for _ in range(5):
        assert client.post(
            "/auth/verify-reset-otp",
            json={
                "email": "admin@example.com",
                "otp": "000000",
                "password": "LockedAdmin123!",
            },
        ).status_code == 400
    assert client.post(
        "/auth/verify-reset-otp",
        json={
            "email": "admin@example.com",
            "otp": locked_otp,
            "password": "LockedAdmin123!",
        },
    ).status_code == 400
    with app.app_context():
        assert PasswordResetOtp.query.count() == 0
    _login(client, "admin@example.com", "TestAdmin123!")


def test_smtp_url_is_normalized_before_delivery(app):
    from app.services.email_service import send_email

    with app.app_context():
        app.config.update(
            MAIL_SERVER="http://smtp.zoho.in/",
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USERNAME="sender@example.com",
            MAIL_PASSWORD="app-password",
            MAIL_DEFAULT_SENDER="sender@example.com",
        )
        with patch("app.services.email_service.smtplib.SMTP") as smtp_class:
            smtp = smtp_class.return_value.__enter__.return_value
            assert send_email(
                "recipient@example.com",
                "Recovery test",
                "<p>Recovery test</p>",
                "Recovery test",
            )

    smtp_class.assert_called_once_with("smtp.zoho.in", 587, timeout=10)
    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with("sender@example.com", "app-password")
    smtp.sendmail.assert_called_once()


def test_brevo_https_delivery_is_preferred_and_safe(app):
    from app.services.email_service import send_email

    with app.app_context():
        app.config.update(
            BREVO_API_KEY="test-brevo-key",
            BREVO_API_URL="https://api.brevo.com/v3/smtp/email",
            BREVO_SENDER_EMAIL="verified@example.com",
            BREVO_SENDER_NAME="Smart Society Test",
        )

        accepted = type(
            "BrevoResponse",
            (),
            {"ok": True, "status_code": 201, "text": '{"messageId":"test"}'},
        )()
        with patch(
            "app.services.email_service.requests.post",
            return_value=accepted,
        ) as post, patch("app.services.email_service.smtplib.SMTP") as smtp:
            assert send_email(
                "recipient@example.com",
                "Recovery test",
                "<p>Recovery test</p>",
                "Recovery test",
            )

        smtp.assert_not_called()
        request = post.call_args
        assert request.args[0] == "https://api.brevo.com/v3/smtp/email"
        assert request.kwargs["headers"]["api-key"] == "test-brevo-key"
        assert request.kwargs["json"]["sender"] == {
            "email": "verified@example.com",
            "name": "Smart Society Test",
        }
        assert request.kwargs["json"]["to"] == [
            {"email": "recipient@example.com"}
        ]
        assert request.kwargs["timeout"] == 30

        rejected = type(
            "BrevoResponse",
            (),
            {"ok": False, "status_code": 400, "text": "sender not verified"},
        )()
        with patch(
            "app.services.email_service.requests.post",
            return_value=rejected,
        ), patch("app.services.email_service.smtplib.SMTP") as smtp:
            assert not send_email(
                "recipient@example.com",
                "Recovery test",
                "<p>Recovery test</p>",
            )
        smtp.assert_not_called()

        app.config["BREVO_API_KEY"] = None


def test_public_app_surfaces(client):
    assert client.get("/health").json == {"status": "ok"}
    assert b"Access Portal" in client.get("/").data
    assert client.get("/assets/css/styles.css").status_code == 200
    recovery_page = client.get("/static/forgot-password.html")
    assert recovery_page.status_code == 200
    assert b"Send Verification Code" in recovery_page.data
    assert b"/auth/verify-reset-otp" in recovery_page.data
    assert b"Facility Operations Console" in client.get("/static/dashboard-admin.html").data
    assert b"Resident Portal" in client.get("/static/dashboard-resident.html").data
    assert b"Technician Workspace" in client.get("/static/dashboard-staff.html").data
    assert client.get("/api-docs/").status_code == 200
    swagger = client.get("/swagger.json")
    assert swagger.status_code == 200
    assert "/auth/verify-reset-otp" in swagger.json["paths"]


def test_complete_complaint_workflow(client):
    admin_headers = _login(client, "admin@example.com", "TestAdmin123!")

    for path in (
        "/admin/dashboard",
        "/admin/complaints",
        "/admin/staff",
        "/admin/reports",
        "/admin/reviews",
        "/categories",
        "/notifications",
    ):
        assert client.get(path, headers=admin_headers).status_code == 200

    staff_password = "TestStaff123!"
    staff_response = client.post(
        "/admin/staff",
        headers=admin_headers,
        json={
            "name": "Henry Walker",
            "email": "henry.walker@example.com",
            "mobile_number": "9876543201",
            "flat_number": "STAFF-04",
            "building": "Maintenance",
            "password": staff_password,
            "trade": "General Maintenance",
        },
    )
    assert staff_response.status_code == 201, staff_response.get_data(as_text=True)
    staff_id = staff_response.json["staff"]["id"]
    staff_headers = _login(client, "henry.walker@example.com", staff_password)

    resident_password = "TestResident123!"
    registration = client.post(
        "/auth/register",
        json={
            "name": "Grace Miller",
            "email": "grace.miller@example.com",
            "mobile_number": "9876543202",
            "password": resident_password,
            "flat_number": "9C",
            "building": "Cedar House",
        },
    )
    assert registration.status_code == 201, registration.get_data(as_text=True)
    resident_id = registration.json["user"]["id"]
    assert client.post(
        "/auth/login",
        json={"email": "grace.miller@example.com", "password": resident_password},
    ).status_code == 403
    assert client.put(
        f"/admin/residents/{resident_id}/approve",
        headers=admin_headers,
    ).status_code == 200
    resident_headers = _login(client, "grace.miller@example.com", resident_password)

    plumbing = Category.query.filter_by(name="Plumbing").first()
    created = client.post(
        "/complaints",
        headers=resident_headers,
        json={
            "category_id": plumbing.id,
            "title": "Bathroom tap will not close",
            "description": "The cold-water tap keeps running even when fully closed.",
            "location": "Cedar House · Unit 9C",
            "priority": "HIGH",
        },
    )
    assert created.status_code == 201, created.get_data(as_text=True)
    complaint_id = created.json["complaint"]["id"]

    with patch("werkzeug.datastructures.FileStorage.save") as save_file, patch(
        "app.services.complaint_service.os.path.getsize",
        return_value=18,
    ):
        attachment = client.post(
            f"/complaints/{complaint_id}/attachments",
            headers=resident_headers,
            data={"file": (io.BytesIO(b"sample image bytes"), "tap-photo.png")},
            content_type="multipart/form-data",
        )
        save_file.assert_called_once()
    assert attachment.status_code == 201, attachment.get_data(as_text=True)

    assigned = client.put(
        f"/admin/complaints/{complaint_id}/assign",
        headers=admin_headers,
        json={"staff_id": staff_id, "remarks": "Inspect the cartridge and isolation valve."},
    )
    assert assigned.status_code == 200, assigned.get_data(as_text=True)

    assert client.get("/staff/dashboard/summary", headers=staff_headers).status_code == 200
    assert client.get("/staff/complaints", headers=staff_headers).status_code == 200
    for status, comment in (
        ("IN_PROGRESS", "Isolation valve closed; replacement cartridge fitted."),
        ("RESOLVED", "Tap tested for ten minutes with no further leakage."),
    ):
        response = client.put(
            f"/staff/complaints/{complaint_id}/status",
            headers=staff_headers,
            json={"status": status, "comment": comment},
        )
        assert response.status_code == 200, response.get_data(as_text=True)

    timeline = client.get(
        f"/complaints/{complaint_id}/timeline",
        headers=resident_headers,
    )
    assert timeline.status_code == 200
    assert len(timeline.json["timeline"]) >= 4

    feedback = client.post(
        f"/complaints/{complaint_id}/feedback",
        headers=resident_headers,
        json={"rating": 5, "comment": "Fast, tidy and professional repair."},
    )
    assert feedback.status_code == 201, feedback.get_data(as_text=True)

    reviews = client.get("/admin/reviews?rating=5", headers=admin_headers)
    assert reviews.status_code == 200
    assert any(
        review["complaint"]["id"] == complaint_id
        for review in reviews.json["reviews"]
    )
