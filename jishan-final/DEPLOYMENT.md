# Free Render deployment

This repository deploys the frontend and Flask API together as one Render web
service. The included `render.yaml` explicitly selects Render's free plan.

Render asks for these deployment secrets:

- `ADMIN_EMAIL`: the email used to sign in to the Smart Society admin portal.
- `ADMIN_PASSWORD`: a new password of at least eight characters for that portal.
- `BREVO_API_KEY`: a Brevo transactional-email API key.
- `BREVO_SENDER_EMAIL`: a sender address that is verified in Brevo.

The Blueprint also sets Brevo's HTTPS endpoint and the sender name. Keep the API
key only in Render's environment; never add it to Git or a frontend file.

The first boot creates a clean SQLite database, seeds that administrator, and
adds realistic example categories, staff, residents, complaint timelines,
notifications and feedback. Demo people have random unusable passwords; they
exist to make dashboards and reports representative without publishing shared
credentials.
No local `.env`, existing database, uploaded files, or old Render URL is
included in the deployment.

## Free-tier limitation

SQLite data and uploaded attachments live on the web service's ephemeral disk.
They can be lost after a restart or redeploy. This keeps the deployment free;
a persistent managed database or disk can be connected later, but must not be
selected if the goal is a zero-cost deployment.

Render Free blocks outbound SMTP ports. Password recovery therefore uses
Brevo's HTTPS API. The optional `MAIL_*` values are intended only for local or
other hosting environments where SMTP traffic is permitted.

Recovery sends a six-digit verification code that expires after 10 minutes,
allows five failed attempts and works only once. Requesting a code never changes
the current password; the password changes only after successful verification.

## Local verification

From the repository root:

```powershell
$env:ADMIN_EMAIL = 'admin@society.com'
$env:ADMIN_PASSWORD = 'Admin@123'
backend\venv\Scripts\python.exe backend\app.py
```

Then open `http://127.0.0.1:5000/`. API documentation is available at
`http://127.0.0.1:5000/api-docs/`, and health checks use `/health`.
