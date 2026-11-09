# Deployment and operations

The supplied Compose file builds a React/Nginx frontend, Python API, extraction worker and one-off migration service around PostgreSQL 16. Only Nginx exposes a host port. API, worker and migration containers use the same environment. API and worker share the upload volume. Images run Python as a non-root user.

Before a public release, terminate HTTPS, configure the exact origin in ALLOWED_ORIGINS, enable COOKIE_SECURE and set a strong database password. Choose a URL-safe database password or percent-encode it when writing DATABASE_URL directly. Do not commit .env files. The sample password in .env.example is a setup placeholder, not a deployed credential.

Run migrations once before starting an updated API/worker. Back up PostgreSQL and the upload volume together; metadata alone cannot restore original documents. Test recovery in a separate environment. Pin image digests in an operational release pipeline.

The API applies login attempt limits in the database per observed client IP and email. Add an ingress-level global rate limit for internet exposure; the trusted-proxy configuration must match your deployment. Monitor queued/failed documents and worker logs. There are no outbound email, account verification or password reset flows in this release.

Health checks test API database connectivity and PostgreSQL readiness. A healthy API does not prove the worker is running; queued items remain visible to the user. The worker reclaims processing leases older than five minutes after interruption. The local SQLite development mode supports one worker; use PostgreSQL for concurrent workers.

The authoring environment did not provide Docker. Compose/Nginx container execution and PostgreSQL concurrency have not been verified there. Verified checks are documented in README. Static preview publication, when supplied, is a fictional frontend demo; it is not the Python deployment.
