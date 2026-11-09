# Architecture and decisions

The browser is a React application with a small data-access hook, typed domain models, comparison calculations, shared forms and dedicated source-document views. Vite builds static assets. Nginx serves the assets and proxies `/api` to FastAPI on the same origin.

FastAPI checks a revocable, opaque session cookie. Only the SHA-256 token hash is stored in the database. Each job, quote, document, expense and export route verifies ownership using server-side joins; the browser never supplies an owner ID. All mutating requests require the custom CSRF header and reject unapproved origins. CORS uses explicit origins and credentials.

PostgreSQL stores users, session hashes, login attempt windows, jobs, quotes, items, source metadata and expenses. Currency is stored as integer fils. Input amounts use Decimal with at most two decimal places; tax rates use basis points. No legal tax rate is hardcoded. Alembic owns the schema; request handlers never create tables.

Uploads are streamed with a size cap, checked by file signature, assigned random storage keys and kept in a shared private volume. SQL document rows form a durable queue. Workers claim queued records with a database lock, commit a processing lease and invoke a bounded parser subprocess. Results include exact page text and candidate excerpts. Parsing failures and manual-review states are explicit. The backend validates source references on quote save.

The comparison engine separates known amounts from confirmed totals. Unknown costs, unreviewed lines and unspecified tax block confirmation. Missing terms generate questions without being treated as invented prices. Quote selection requires a complete total. Job scope equivalence remains a user judgment.

The account workspace and anonymous demo are separate. The demo has no real documents, users or network persistence. React derives demo summaries using the same money rules as the backend. The production API remains the authoritative calculator for signed-in data.

## Deliberate boundaries

There is no marketplace, bank/payment connection, provider verification, paid AI API, OCR, automatic quote recommendation, email delivery or automatic WhatsApp sending. The worker is a persistent SQL queue, not a claim of unlimited parallel processing. A single shared upload volume is appropriate for the supplied single-host Compose setup; a multi-host deployment should use private object storage with equivalent authorization.
