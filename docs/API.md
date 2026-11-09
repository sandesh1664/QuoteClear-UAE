# API and data model

Interactive OpenAPI is exposed at `/api/docs`. JSON endpoints return Pydantic validation errors with 422, missing authentication with 401, invalid request origin/header with 403, and non-owned resources with 404. All account data is scoped to the session user.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create account and session |
| POST | `/api/auth/login` | Start session |
| GET | `/api/auth/me` | Current account |
| POST | `/api/auth/logout` | Revoke current session |
| GET / POST | `/api/jobs` | List / create jobs |
| GET / PUT / DELETE | `/api/jobs/{id}` | Read, edit or remove an owned comparison |
| POST | `/api/jobs/{id}/quotes` | Add a quote and its items |
| PUT / DELETE | `/api/quotes/{id}` | Replace / remove an owned quote |
| POST | `/api/jobs/{id}/selection` | Select a complete quote or clear selection |
| POST | `/api/jobs/{id}/documents` | Queue source upload (multipart form field `file`) |
| GET | `/api/documents/{id}` | Extraction status and page text |
| GET | `/api/documents/{id}/file` | Private original-file download |
| POST | `/api/documents/{id}/retry` | Requeue a completed/failed extraction |
| POST | `/api/jobs/{id}/expenses` | Record actual payment |
| DELETE | `/api/expenses/{id}` | Remove a recorded payment |
| GET | `/api/jobs/{id}/report.pdf` | Generate comparison PDF |
| GET | `/api/jobs/{id}/export` | Export comparison JSON |
| GET | `/api/health` | Database connectivity probe |

Mutation requests use `X-QuoteClear: 1` and the session cookie. The frontend includes both. Money inputs/outputs are decimal strings in AED. Item `amount` is a unit price; quantity is an integer. Pricing is `fixed`, `included` or `unknown`. `reviewed` must be explicitly set. Included lines have no extra charge; unknown lines have no invented zero-cost assumption.

Relations: User → Jobs → Quotes → LineItems; Job → Documents; Quote optionally references a Document from the same Job; Job → Expenses; User → Sessions. Selected quote IDs are validated against their job before saving. Deleting a comparison explicitly removes its descendants and private original files. Deleting a selected quote clears the job selection.
