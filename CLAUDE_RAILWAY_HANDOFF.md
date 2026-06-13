# QuizCat Operations Handoff

## Ownership

- Canonical GitHub repository: https://github.com/micronox/QuizCat
- Default branch: `main`
- Railway workspace: `micronox's Projects`
- Railway project: `quizcat-textual`
- Railway project ID: `ffa41b8d-4009-411b-ad20-0130c9c2328a`

The Railway project contains two applications and one shared Postgres database.
The services must be deployed separately because they use different project
roots and start commands.

## Live Services

| Resource | Public URL | Start command |
| --- | --- | --- |
| `quizcat-web` | https://quizcat-web-production.up.railway.app | `npm run start` from `web/` |
| `quizcat-textual` | https://quizcat-textual-production.up.railway.app | `python serve.py` from repository root |
| `Postgres` | Private Railway resource | Railway-managed PostgreSQL |

Both public services use `/` as their Railway health-check path.

## Current Verification

Verified on June 13, 2026:

- Both Railway app services and Postgres report `SUCCESS`.
- Both public home pages return HTTP `200`.
- Next.js routes `/api/tests`, `/quiz/1`, `/stats`, and a question image return
  HTTP `200`.
- Postgres contains 400 questions, 1,952 choices, 8 tests, and 400
  test-question links.
- `npm run lint`, `npm run build`, and all 19 Python tests pass locally.
- GitHub Actions CI covers the Python tests and Next.js lint/build on pushes and
  pull requests.

## Safe Deployment Commands

The Railway CLI may be linked to either application. Always name the target
service explicitly.

Deploy the Textual browser app:

```powershell
railway up --service quizcat-textual --detach
```

Deploy the Next.js/Postgres app:

```powershell
railway up web --path-as-root --service quizcat-web --detach
```

Check status and logs:

```powershell
railway status
railway logs --service quizcat-textual --latest --lines 100
railway logs --service quizcat-web --latest --lines 100
railway logs --service Postgres --latest --lines 100
```

Run local checks:

```powershell
uv sync --extra dev
uv run python -m pytest
cd web
npm ci
npm run lint
npm run build
```

Use `pytest`, not bare `unittest discover`; the latter does not recurse into the
current non-package `tests/` directory and can misleadingly report zero tests.
The Python app uses `uv` as its environment manager and is not configured as an
installable Python package, so do not use `pip install -e .` in CI.

## Database Operations

`quizcat-web` receives `POSTGRES_URL` through a Railway reference to the
`Postgres` service. Never commit the resolved connection string.

Schema migration and seed commands are idempotent:

```powershell
cd web
npm run db:migrate
npm run db:seed
```

The seed reads `../ccat_full_question_bank_prompt_stimulus.csv`. Review dataset
changes before reseeding production.

## Flagged Issues

### Public app has no authentication

`quizcat-web` is intentionally single-user and has no authentication. Anyone
with the public URL can start quizzes and view shared stats. Add authentication
or make the service private before treating attempt data as private.

### Railway deployments are manual uploads

Both app services currently have no connected GitHub source. Deployments are
performed with `railway up`; pushes to GitHub do not automatically deploy.
This avoids accidental monorepo root confusion, but requires an explicit deploy
after production changes. GitHub auto-deploy can be enabled later only after
confirming separate root-directory settings for both services.

### Dependency audit warning

`npm audit` currently reports two moderate vulnerabilities through Next.js'
bundled PostCSS dependency. The suggested automatic fix downgrades Next.js
across a major version and should not be applied blindly. Reassess when a
compatible Next.js release resolves the advisory.

### Postgres startup warning

The Railway Postgres log includes a one-time
`collation-refresh ... Permission denied` warning during initialization. The
database subsequently reports ready, remains healthy, and serves queries. Flag
it for investigation if it recurs during restarts or database behavior changes.

## Recovery

- Do not force-push `main` unless the remote branch has been inspected and its
  additional work preserved.
- A local backup of the earlier deployment history exists as
  `local-deployment-history`.
- Railway service IDs and the Postgres volume are visible through
  `railway service list --json`.
- Before changing or deleting Postgres, export or back up production data.
