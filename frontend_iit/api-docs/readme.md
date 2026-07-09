# Smart Society API Docs (Team Sputnik)

Interactive Swagger UI for the Complaint Resolution System API contract,
shared between the Vue 2 frontend and the FastAPI backend.

## What's in here
- `openapi.yaml` — the API contract (single source of truth). Edit this
  whenever an endpoint changes; everyone's docs update automatically.
- `index.html` — a static page that loads `openapi.yaml` into Swagger UI
  (via CDN, no build step, no `npm install` needed).
- `vercel.json` — makes sure `openapi.yaml` is served with the right
  content type and CORS headers.

## Deploy to Vercel (so the whole team can access it)

### Option A — via GitHub (recommended for a 5-person team)
1. Push this folder to a new GitHub repo, e.g. `smart-society-api-docs`.
2. Go to https://vercel.com/new, click **Import Git Repository**, select the repo.
3. Framework preset: choose **Other** (it's static, no build command needed).
4. Click **Deploy**. Vercel gives you a URL like
   `https://smart-society-api-docs.vercel.app`.
5. In Vercel → Project → Settings → **Members**, invite your 4 teammates
   by email (or add them to your Vercel Team so every project is shared).
6. Anyone on the team can now open the URL and see the live, interactive docs.
   Every time someone pushes an updated `openapi.yaml`, Vercel redeploys automatically.

### Option B — quick deploy from your machine (no GitHub needed yet)
```bash
npm i -g vercel        # one-time install
cd api-docs
vercel login
vercel --prod
```
Vercel will print the live URL — share that with the team.

## Local preview (before deploying)
No build tools required — just serve the folder:
```bash
cd api-docs
python3 -m http.server 8080
# open http://localhost:8080
```

## Connecting this to the real FastAPI backend later
FastAPI auto-generates its own Swagger UI at `/docs` from your route
definitions — but that only reflects what's actually been *built*, and only
works while the backend server is running. This standalone `openapi.yaml`
is meant to be the **agreed-upon contract** you design first, so frontend
(Vue) and backend (FastAPI) devs can build in parallel against the same spec.

To keep them in sync later:
- You can hand-copy the path/schema definitions into FastAPI's `APIRouter`
  + Pydantic models as you implement each endpoint, **or**
- Use a generator like `datamodel-code-generator` to turn `openapi.yaml`
  schemas straight into Pydantic models:
  ```bash
  pip install datamodel-code-generator
  datamodel-codegen --input openapi.yaml --output models.py
  ```

## Editing the spec
Edit `openapi.yaml` directly — it's plain YAML. Validate it before pushing
with the [Swagger Editor](https://editor.swagger.io) (paste contents in) or:
```bash
npx @redocly/cli lint openapi.yaml
```

