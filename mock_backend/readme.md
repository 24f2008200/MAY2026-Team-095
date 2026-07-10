# Smart Society Mock Backend

A deterministic mock/stub Flask server implementing every endpoint in
`openapi.yaml` (Smart Society Complaint Resolution System, Team Sputnik,
MAY2026-Team-095), so the Vue frontend team can build against real request
shapes without waiting for the FastAPI backend.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Server starts at **http://localhost:8000/v1/**. Visit `http://localhost:8000/v1`
in a browser for a full list of routes.

## How response control works

Every route resolves a status code (200/201/401/404/409/etc.) using one of
three mechanisms, in priority order:

### 1. Force ANY status with `?_status=`

Works on every single endpoint, regardless of what's documented in the spec.
Great for testing error UI (spinners, toasts, empty states) that aren't even
in the OpenAPI contract yet:

```
GET  /v1/complaints/C-1001?_status=500
PUT  /v1/staff/complaints/C-1001/status?_status=403
```

### 2. Checksum on a "primary field"

For endpoints with more than one documented response, the field's checksum
(sum of character codes) modulo the number of documented responses picks
which one comes back — same input always gives the same output:

| Endpoint | Primary field | Documented responses |
|---|---|---|
| `POST /auth/register` | `email` | `[201, 409]` |
| `POST /auth/login` | `usernameOrEmail` | `[200, 401]` |
| `GET /complaints/{id}` | `complaintId` (path) | `[200, 404]` |

Example:
```json
POST /auth/register
{ "email": "pbn@example.com", "name": "PBN" }
```
`checksum("pbn@example.com") % 2` deterministically resolves to `201` or `409`
— always the same result for that exact string.

### 3. Force an exact index with `#N`

Append `#N` to the primary field value to force `documented[N]` regardless
of checksum, without needing the query string trick:

```json
{ "email": "pbn@example.com#0" }   // always 201
{ "email": "pbn@example.com#1" }   // always 409
```

This works for path params too — just URL-encode the `#`:
```
GET /v1/complaints/C-1001%231     -> forces 404
```

### No control given

The route just returns its "happy path" response with realistic fake JSON
(random but schema-shaped Users, Complaints, Notifications, etc.).

## Logging

Every request logs which field was used, its checksum, the documented list,
and the final status, e.g.:

```
POST /auth/register   primary='pbn@example.com' checksum=1042 documented=[201, 409] -> idx=0 method=checksum_modulus status=201
```

## Files

| File | Purpose |
|---|---|
| `app.py` | All Flask routes (one per OpenAPI operation) |
| `checksum.py` | Checksum, `#N` override, and `_status` override logic |
| `fake_data.py` | Realistic fake payload builders per schema (User, Complaint, Notification, ...) |
| `requirements.txt` | Flask, Flask-Cors |

## Notes / things you may want to adjust

- CORS is wide open (`Flask-Cors` with defaults) — fine for local dev, lock
  it down before this touches anything real.
- List endpoints (`GET /complaints`, `GET /admin/complaints`, etc.) return a
  fixed count of randomly generated items each call; they don't persist
  state between requests. If you need stateful behavior (e.g. POST then GET
  returns what you just created), that's a bigger step up from a stub and
  worth a follow-up if you need it.
- `multipart/form-data` routes (`POST /complaints`, `PUT /staff/complaints/{id}/status`)
  read whatever form fields you send; uploaded files are counted, not stored.
