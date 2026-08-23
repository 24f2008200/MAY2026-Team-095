# Smart Society Complaint Resolution System

Smart Society is a full-stack apartment-maintenance portal for residents,
technicians and administrators. It combines a Flask REST API with a responsive
HTML/CSS/JavaScript frontend and ships with realistic sample records so every
dashboard is useful immediately after deployment.

## Live deployment

- Application: <https://smart-society-hrsw.onrender.com/>
- API documentation: <https://smart-society-hrsw.onrender.com/api-docs/>
- Health endpoint: <https://smart-society-hrsw.onrender.com/health>
- Hosting: Render Free web service

Demo administrator:

```text
Email:    admin@society.com
Password: Admin@123
```

These credentials are intentionally provided for academic demonstration. Use
different secrets for any non-demo deployment.

## Capabilities

- Resident registration with administrator approval.
- Role-based resident, technician and administrator dashboards.
- Complaint creation, attachments, priorities and categories.
- Administrator dispatch and reassignment based on technician trade.
- Technician work-status updates and full complaint timelines.
- Resident closure, reopening and five-star feedback.
- Staff performance, records, notification and approval views.
- Password recovery email through Brevo's HTTPS API.
- OpenAPI/Swagger documentation and a deployment health endpoint.
- Six realistic complaints covering plumbing, electrical, elevators, access,
  HVAC and waste management.

## Workflow

```text
OPEN / REOPENED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
```

Only administrators assign work. Technicians can update only their assigned
complaints. Residents can see only their own complaints and may reopen an
eligible resolved or closed complaint. The detailed rules are documented in
[WORKFLOW_AUDIT.md](WORKFLOW_AUDIT.md).

## Technology

- Python 3.11 and Flask 3
- Flask-RESTX, JWT, SQLAlchemy and Marshmallow
- SQLite by default; `DATABASE_URL` can select another SQLAlchemy database
- Vanilla HTML, CSS and JavaScript frontend
- Gunicorn on Render
- Brevo transactional email over HTTPS

## Project structure

```text
.
|-- backend/
|   |-- app/                 Flask application, routes, services and models
|   |-- migrations/          Alembic database migrations
|   |-- tests/               Deployment and end-to-end workflow tests
|   `-- requirements.txt
|-- frontend/
|   |-- assets/              Shared styles
|   |-- images/              Logo and favicon
|   |-- js/                  Shared browser utilities and state
|   `-- static/              Role dashboards and workflow pages
|-- .env.example             Safe configuration template
|-- render.yaml              Free Render Blueprint
|-- DEPLOYMENT.md            Deployment guide
`-- README.md
```

## Run locally

Requirements: Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
python backend\app.py
```

Open <http://127.0.0.1:5000/>. Edit `.env` before starting if you need real
email delivery. `.env` is ignored by Git and must never be committed.

Linux/macOS users can activate with `source .venv/bin/activate`, copy with
`cp .env.example .env`, and otherwise use the same commands.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Production | Flask signing secret |
| `JWT_SECRET_KEY` | Production | JWT signing secret |
| `ADMIN_EMAIL` | Yes | Creates or rotates the administrator email |
| `ADMIN_PASSWORD` | Yes | Creates or rotates the administrator password |
| `SEED_DEMO_DATA` | No | Adds realistic starter data when `true` |
| `DATABASE_URL` | No | Defaults to local SQLite |
| `BREVO_API_KEY` | Email | Brevo transactional-email API secret |
| `BREVO_API_URL` | No | Defaults to Brevo's v3 send endpoint |
| `BREVO_SENDER_EMAIL` | Email | Sender verified in Brevo |
| `BREVO_SENDER_NAME` | No | Human-readable sender name |
| `RECOVERY_TEST_EMAIL` | No | Maps the Emily Carter demo account to a private test inbox |

SMTP `MAIL_*` variables remain an optional fallback for environments that
permit outbound SMTP. Render Free blocks SMTP ports, so its deployment uses
Brevo over HTTPS.

## Password recovery safety

The request endpoint always returns a generic success response for unknown
addresses, preventing account enumeration. For a registered account it asks
Brevo to deliver a cryptographically generated six-digit verification code.
Codes expire after 10 minutes, allow five failed attempts and work only once.
The recovery screen does not show or accept a new password until the code is
verified. Verification issues a short-lived one-time reset token, and only that
token can authorize the final password change. A provider rejection returns a
safe error and leaves the existing password usable.

## Tests

From `backend` with the virtual environment active:

```powershell
python -m pytest -q -p no:cacheprovider tests\test_deployment_smoke.py
```

The suite covers seed idempotence, administrator rotation, Brevo and SMTP
delivery behavior, OTP expiry, attempt limits, one-time use, recovery failure
safety, login edge cases, authorization, registration and approval, staff
creation, attachments, complaint assignment, status transitions, timelines and
resident feedback.

## Free-hosting notes

Render Free instances sleep after inactivity and can take roughly a minute to
wake. Their filesystem is ephemeral, so SQLite records and uploaded files may
reset after a restart or redeploy. This is suitable for a free academic demo;
use a persistent managed database and object storage for production.

## Security

- No API keys, mailbox passwords, `.env` files or databases are committed.
- Configure secrets in the hosting provider's environment settings.
- Rotate any credential that is accidentally exposed.
- The supplied administrator is a demo credential and should not protect real
  resident data.
