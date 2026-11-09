# QuoteClear UAE

**Clarity before commitment.** A full-stack quotation comparison workspace for UAE residents and small businesses. Created for Sandesh Joshi.

Compare the complete price of the same job across providers, retain source documents, identify unanswered questions, and record what you actually pay. This is an independent personal workspace, not a provider marketplace or a price-verification service.

## Features

- Email/password accounts with Argon2 password hashing and revocable HttpOnly server sessions.
- Private jobs and quotations, with cost items, quantities, known/included/unknown pricing and explicit review checkboxes.
- Confirmed totals only when every cost is priced or included, reviewed and has explicit tax treatment.
- Integer fils and decimal half-up tax calculations, mirrored in the frontend and covered by tests.
- Side-by-side comparison of cost, tax, warranty, completion time, quote validity and exclusions.
- Original PDF/JPEG/PNG attachments with SHA-256 hashes and authenticated downloads.
- Durable SQL extraction queue and separate Python worker. Text-PDF amounts include exact page and text references.
- Source-reference validation: a stored excerpt must actually occur on the selected page of a document belonging to the same job.
- Editable provider-clarification messages, copy and user-initiated WhatsApp sharing.
- Quote selection, actual spending records, PDF reports and JSON exports.
- Mobile layouts, native accessible dialogs and an explicit fictional demo that resets on reload.

## Stack

| Layer | Implementation |
| --- | --- |
| UI | React 19, TypeScript, Vite, Lucide icons, responsive CSS |
| API | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL in Docker; SQLite for local development and tests |
| Migrations | Alembic, committed initial migration |
| Extraction | pypdf in a resource-limited subprocess; durable SQL worker queue |
| Reports | ReportLab PDF generation |
| Delivery | Docker Compose, Nginx reverse proxy, pinned Python and npm lockfiles |

## Run the full project

Requires Docker Engine/Desktop with Compose v2.

```sh
git clone https://github.com/sandesh1664/QuoteClear-UAE.git
cd QuoteClear-UAE
cp .env.example .env
# Edit .env and replace POSTGRES_PASSWORD with a long random password.
docker compose up --build -d
```

Open **http://localhost:8080**. Create your account using Sign in → Create an account. A signed-in workspace starts empty; the anonymous demo is fictional and never writes into your account.

API documentation: **http://localhost:8080/api/docs**. API and extraction-worker logs: `docker compose logs -f backend worker`. Stop without deleting data: `docker compose down`. PostgreSQL and uploaded originals live in named volumes. Do not delete volumes if you need to retain your records.

Docker was not available in the authoring environment, so the Compose stack has not been executed there. Backend API/extraction tests and the frontend build are verified separately. PostgreSQL is the configured deployment database; automated tests run on isolated SQLite databases.

## Local development without Docker

Backend, terminal 1:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Worker, terminal 2 (same backend directory and environment):

```sh
source .venv/bin/activate
python -m app.worker
```

Frontend, terminal 3:

```sh
cd frontend
npm ci
npm run dev
```

Vite proxies `/api` to port 8000. Use the frontend URL printed by Vite (normally http://localhost:5173). A stopped worker leaves uploads queued; restart the worker to process them. Stale processing leases are requeued after five minutes. Use one extraction worker with SQLite; PostgreSQL supports worker claims with `SKIP LOCKED`.

## Tests and build

```sh
cd backend
.venv/bin/python -m pytest -q
cd ../frontend
npm test
npm run build
```

The backend suite tests login/logout, cookie flags, CSRF/origin checks, account isolation, precise tax rounding, selection invalidation, actual spending, PDF reporting, upload checks, the extraction worker and exact provenance. Frontend domain tests verify integer money and incomplete-total rules.

## How comparison works

1. Create a job and describe its scope.
2. Add each provider's line items. Record unknowns as **Unknown**, not zero.
3. Explicitly enter tax treatment; no statutory rate is assumed by the app.
4. Review each amount. Unreviewed or unknown amounts keep the final total incomplete.
5. Ask about missing warranty, delivery, validity or exclusions.
6. Select a complete quote and record deposits/final payments as they occur.

The lowest confirmed total is a price comparison, not a recommendation about quality or provider reliability. Missing terms remain visible even when a total is complete. Editing a selected quote so its total becomes incomplete clears the selection.

## Documents and extraction boundaries

Text PDFs up to 10 MB and 40 pages are supported. The worker finds **currency-labelled** amounts, not complete semantic quotations. A detected total, subtotal or tax amount can all appear as candidates; the user must identify what it means and avoid double counting. Nothing is auto-approved. Original files are downloaded as attachments and are never served from a public directory.

Images and scanned PDFs can be attached, but **OCR is not implemented** in this release. They are marked for manual entry. PDF parsing uses a separate process with a timeout and Linux memory/CPU limits. Hashes identify file bytes; they do not prove who issued a quote or provide a trusted external timestamp.

PDF and JSON exports include comparison data and source references, not copies of uploaded original files. Download originals separately. A JSON export is a report format; automatic restore/import is not implemented.

## Demo and hosting

The complete app needs Python, PostgreSQL and persistent file storage. Static hosts and GitHub Pages cannot run the backend. A frontend-only preview can be built using:

```sh
cd frontend
VITE_DEMO_ONLY=true npm run build
```

That preview is explicitly temporary sample data. Account creation, uploads and server-generated reports require the full backend. Demo reports use the browser print dialog. Source code remains the complete full-stack application.

For internet deployment, place the Nginx service behind HTTPS, set `ALLOWED_ORIGINS` to your exact origin and `COOKIE_SECURE=true`, set a strong database password, persist and back up both volumes, and configure your proxy's request limits. Session state is database-backed, not stored in localStorage. Registration can be closed with `ALLOW_REGISTRATION=false`. Self-service email verification and password recovery are not included; do not describe this release as a finished multi-tenant commercial service without adding those operational flows.

See [architecture](docs/ARCHITECTURE.md), [API and data model](docs/API.md), and [deployment notes](docs/DEPLOYMENT.md).
