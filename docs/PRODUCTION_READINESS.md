# Backend deployment and capacity report

Review date: 20 September 2026. Scope: existing GradAlumni backend, configuration, dependencies, migrations, API regression tests and local HTTP load. No production deployment, remote database mutation or real email delivery was performed.

## Release decision

**Deployment preparation is implemented, but production readiness for 1,000 concurrent active users is NOT certified.** The local high-load runs have latency/error failures. The configured remote database also failed its read-only connectivity check. Do not interpret worker or connection limits as measured capacity.

The private `.env` was inspected through a redacted preflight. It was not copied into documentation or overwritten. Current findings:

- `APP_ENV` is `development`.
- Database is remote PostgreSQL with a TLS option; a read-only connection/schema check timed out. Resolve database reachability before release.
- JWT secret meets the length check. Production startup also rejects low-diversity placeholder secrets.
- CORS includes non-HTTPS origins. Set only real HTTPS frontend origins for production.
- `ALLOWED_HOSTS` and `REDIS_URL` are absent.
- SMTP and a document-storage path are configured; SMTP delivery was not exercised.

Use `python scripts/check_environment.py --connect` to repeat the redacted read-only check. It does not migrate, seed, load-test or modify the target database.

## Implemented hardening

| Area | Change |
| --- | --- |
| Dependencies | Patched FastAPI/Starlette, dotenv and multipart; replaced python-jose with PyJWT to remove its unpatched ecdsa dependency. Runtime and development requirements are separate. Production dependency audit reports no known vulnerabilities at review time. |
| Authentication | Explicit HS256 verification and required expiry/subject; production rejects unrevocable legacy tokens and legacy registration bypasses. Existing users must sign in again for session-backed tokens. Password hashing/verification uses a bounded thread pool. |
| Professional verification | Changing domain, discipline or organization clears verification; professional assessment permissions must be reverified. |
| Request controls | Shared atomic Redis quotas in production; authenticated-user quotas avoid combining all signed-in campus users into one general IP quota. Auth actions remain IP-limited. Redis failure returns 503 instead of bypassing protection. Body size is bounded, including chunked bodies. |
| Database | Explicit pool size, overflow and wait/command timeouts; sanitized DB errors, hidden SQL parameters, new query indexes and proper shutdown disposal. Authentication loads session/user in one query. |
| Recommendations | Candidate evidence loaded once; recommendation generation uses six queries rather than repeated queries per opportunity. Regression test checks output parity and query count. |
| Messaging | Latest 100 messages by default, up to 200 per page, before/after cursors, indexed queries, five-second incremental socket catch-up and release of DB connections before socket sends. Frontend supports older-message loading. |
| Documents | PDF extraction and certificate rendering run outside the event loop with bounded concurrency. Persistent storage paths are configurable for both upload systems. |
| Mail | Verified SMTP TLS, support for TLS-on-connect port 465, one-message transactions, optional continuous worker. Successful mail is committed before a later message failure. Delivery remains at-least-once if a process crashes after SMTP acceptance but before commit. |
| Operations | `/health` is liveness; `/ready` checks DB connectivity, expected migration revision and Redis. Production docs disabled by default. Trusted hosts, security headers and request IDs; logs omit credentials, query strings and SQL values. |
| Packaging | Non-root Docker image, private build exclusions, shared persistent document volume, bounded Uvicorn workers, graceful shutdown, separate migration release step, TLS reverse-proxy example and CI workflow. |

Redis uses atomic `INCR`/`EXPIRE` in a Lua script as described in [Redis rate-limiter guidance](https://redis.io/docs/latest/commands/incr/). Worker/concurrency controls follow [Uvicorn settings](https://www.uvicorn.org/settings/); a concurrency ceiling can return 503 and is not a throughput promise. PostgreSQL pooling should be budgeted across all workers/replicas; see [SQLAlchemy PostgreSQL guidance](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).

## Capacity measurements

Local Windows machine, 8 logical CPUs, four API workers, isolated PostgreSQL 18, 1,000 synthetic student identities, 10,000 skill scores and 25 published opportunities. The generator and server share the machine. Requests rotate among account profile, opportunity list, own skills and recommendations. No remote/live data was used.

| Run | Requests | Outcome | Client p95 | Notes |
| --- | --- | --- | --- | --- |
| Initial 1,000-user ramp | 3,000 | 2,996 HTTP 200; 4 protocol errors | 26,093 ms | Shared generator pool incurred substantial client overhead; retained as a failed run |
| 1,000-user ramp, sharded generator | 3,000 | 2,999 HTTP 200; 1 HTTP 503 | 4,917 ms | Default DB budget: four workers × (10 + 5) = 60 maximum connections |
| 1,000-user ramp, larger pool | 3,000 | 2,974 HTTP 200; 26 HTTP 503 | 7,477 ms | 80 connections worsened performance; not adopted as default |
| 100-user baseline after authentication optimization | 500 | 500 HTTP 200 | 292 ms | Peak 28 requests in flight; this is not 100 simultaneous requests |

Raw results live in ignored `tmp/load-*.json`. The final validation report may add a later run below. These are short synthetic checks, not soak tests. Login bursts, file uploads, WebSocket concurrency, Redis overhead, TLS and WAN latency are excluded. Functional tests use a shared-counter substitute for Redis; an actual Redis deployment was not available locally. Docker was not installed, so container execution has not been verified here.

A release test must use the actual Linux hosting plan and database in the same region, a separate load generator and real Redis. Suggested acceptance gates: p95 below 2 seconds, p99 below 5 seconds, unexpected errors below 0.1%, stable memory/CPU/DB connections during at least a 30-minute representative run. Agree on how often each of the 1,000 users sends a request; 1,000 signed-in users and 1,000 simultaneous requests are different workloads.

## Deployment procedure

1. Provision the selected server, PostgreSQL, Redis and HTTPS ingress. A four-worker configuration is a starting configuration to benchmark, not a capacity guarantee. Check the database provider's actual connection allowance before changing pool settings. Default API connection budget is 60, plus migration, mail and administration connections.
2. Update private `.env` with real HTTPS frontend origins, API hosts and shared services using `.env.production.example` as a checklist. For Docker, compose supplies its private Redis URL and Linux storage paths. Preserve the existing database/JWT secrets. Set `FORWARDED_ALLOW_IPS` to the actual trusted proxy IP/CIDR; the app must not be directly exposed to untrusted clients that can forge forwarding headers.
3. Back up the database and uploads, and verify that both backups can be restored. Do not rely on the container writable layer for documents. These backup operations have not been executed on the user's database.
4. Build and start Redis; then run migrations once. The new revision is `ga20_production`, following `ga20_delivery`. Its indexes should be created before traffic or in a maintenance window for populated tables.

```powershell
cd D:\SIH\Backend-Grad
docker compose -f compose.production.yaml build
docker compose -f compose.production.yaml up -d redis
docker compose -f compose.production.yaml run --rm api python -m alembic upgrade head
docker compose -f compose.production.yaml up -d api
```

5. Install the TLS proxy configuration from `deploy/nginx.conf.example` using real hostname/certificate paths. API port 8000 is loopback-only in compose. Ensure `localhost` is in `ALLOWED_HOSTS` for the container health check. Validate `/ready` through ingress, then exercise signup/verification, each role, uploads, assessment, application, feedback and certificate download.
6. Run the mail worker under a process supervisor only when ready to send queued transactional mail. `python scripts/deliver_mail.py --loop` uses the configured SMTP credentials. It was not run during this review.
7. Load-test staging with the acceptance gates above before routing real users. Monitor p95/p99, 429/503 rates, pool waits, CPU/memory, Redis health, SMTP queue and disk usage. Request logs are available; a metrics/alerting service is not provisioned by these changes.

`compose.yaml` remains the local development stack. `compose.production.yaml` uses the existing external database. `render.yaml` is also updated with a release migration command, readiness health check and persistent upload disk, but needs an appropriate paid plan, Redis and private environment variables before deployment. Render documents paid-plan requirements for [pre-deploy commands](https://render.com/docs/deploys) and [persistent disks](https://render.com/docs/disks). A disk-attached service cannot scale to multiple instances; move documents to shared/object storage for that topology. No Render service has been provisioned.

Multiple workers on one server share the document volume. Multiple servers require shared/object storage before horizontal scaling. WebSockets still use bounded database polling; benchmark that workload separately and add shared message notifications for a larger real-time deployment.

## Repeatable tests

Completed validation: **32 SQLite backend tests passed; 31 PostgreSQL tests passed and one thread-bridged WebSocket test skipped; 16 frontend tests passed; production frontend build passed; fresh-database migrations, incremental migration and Alembic schema comparison passed; runtime dependency audit covered 46 packages with zero known findings; `pip check`, Python compilation and focused lint passed.** Two dependency deprecation warnings remain in the test-client stack. Docker execution, real Redis, TLS ingress, live SMTP and staging soak tests remain unverified.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\.venv\Scripts\python.exe -m compileall -q app scripts
```

For PostgreSQL tests set `TEST_DATABASE_URL` to an isolated test instance; each test uses a temporary schema. Never point it at production. `scripts/prepare_load_fixture.py` refuses any database other than localhost `gradalumni_load`; `scripts/load_test.py` refuses remote targets. CI runs SQLite and PostgreSQL suites, migration checks and dependency auditing. The tests cover business/security regressions, not every possible branch of all 350 HTTP operations.
