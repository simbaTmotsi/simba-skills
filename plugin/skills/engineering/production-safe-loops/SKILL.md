---
name: production-safe-loops
description: Check what a feedback loop will actually write to before running it, and refuse to run it against production. Use before running a test suite with database fixtures, a repro or curl loop, a replay script, a stress loop ("loop the trigger 100x, parallelise"), a migration, an import, or a seed script. Use whenever you are about to run tests, build a repro loop, or debug against a running system, and especially when following TDD or bug-diagnosis skills (such as `tdd` or `diagnosing-bugs`) in a repo whose live deployment runs on the same host, shares its `.env`, or is reachable from the shell.
---

# Production-safe feedback loops

A feedback loop runs many times, unattended, and writes wherever its config points. If that is production, every red run corrupts real data. Before the **first** run of any loop with side effects, find out what it writes to. If the answer is production, or you cannot tell, do not run it.

## 1. Resolve the real target before the first run

Do not trust the variable name. Resolve what the loop will see at runtime:

- **Env files**: which `.env` (or `.env.local`, `.env.test`, settings module) the test runner, framework, or script actually loads, and in what order. Print the resolved `DATABASE_URL`, `REDIS_URL`, queue, search, storage, and API base URL values (with credentials redacted).
- **Fixtures**: what the test setup (`conftest.py`, global setup, factories) connects to. Fixtures write to whatever `DATABASE_URL` resolves to, and some truncate or drop tables.
- **Containers**: the compose project name, container names, and which network and volumes they share. A container being "local" does not make it non-production.
- **HTTP targets**: the base URL a curl, replay, or browser script hits.

**The common trap:** the repo `.env` points at the production database because production runs from the same checkout or host. A plain test run then writes fixtures straight into production. Assume this until you have proved otherwise.

## 2. How to tell if a target is production

Treat the target as production if **any** of these hold:

- [ ] Its database, container, or compose project name contains `prod`, `production`, `live`, `main`, or the product's bare name with no `test` or `dev` marker.
- [ ] It is the database or service that the running deployment (the web or worker containers serving users) is connected to.
- [ ] It holds real user or customer rows, or row counts far beyond what fixtures create.
- [ ] Its URL is the public domain, a non-loopback host, or a managed cloud endpoint.
- [ ] Its volume is backed up, or a deploy or restart script references it.
- [ ] You cannot say for certain which of the above is true.

## 3. Run loops only against isolated targets

- Prefer isolated, disposable test containers, or a project test-env script that sets the test env and **refuses to start if the target looks like production**. If the repo has one, use it for every red and green run.
- If there is none, propose one to the user (a separate database and cache on separate ports, with a guard that exits on a production URL) instead of improvising against the shared env.
- Pure unit tests with no database, network, or filesystem side effects can run with the plain test runner.
- **Never run tests inside production containers** (the web, worker, or scheduler containers serving users), even "just one test".
- Curl, CLI, replay, and browser loops target a local dev server or the test containers, never the live domain or the production containers.
- Keep each loop on the **narrowest target**: one test id, one endpoint, one record. Widen only when the narrow loop is green.
- Stress loops (100x, parallel) multiply side effects. Run them only against a target you have already verified is isolated.

## 4. What needs explicit approval

Reading production is fine for diagnosis: logs, container status, read-only queries, metrics.

Anything that changes production needs the user's explicit yes in the current conversation **before** it runs:

- Restarts, rebuilds, and redeploys (for deploys, tell the user to run `/safe-deploy`).
- Migrations, imports, seed scripts, backfills, and data fixes.
- Production instrumentation: extra logging, debug flags, feature toggles, temporary endpoints.

State exactly what will run, against which target, and how to roll it back. Silence or an earlier general approval is not a yes.

## 5. Redact what you show

Loop output is shown to the user and often pasted elsewhere. Redact secrets (passwords, tokens, connection strings, keys) and personal data (names, dates of birth, emails, phone numbers, account and identity numbers) from command output, logs, and captured payloads. Save captured production artifacts for replay only after redaction.

## 6. If you cannot make it safe

Stop and say so. Report what the loop would write to and why it is unsafe, then ask for one of: an isolated environment, a redacted captured artifact to replay locally, or explicit approval for a specific, bounded action. Do not run the loop "once to see".
