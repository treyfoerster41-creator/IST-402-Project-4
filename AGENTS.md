# Assignment 4 — Signal Desk

Use Vue, FastAPI and SQLite on localhost. Parts 4.1–4.3 are cumulative. Current scope is Part 4.2: preserve Part 4.1 live streaming/persistence and add SMA crossover, simulated accounting, historical backtesting, browser tests and GitHub Actions. All trading is simulated; no broker or real-money integration.

- Backend owns Yahoo integration, validation, append-only observation revisions, candle aggregation, SQLite initialization and API/WebSocket routes. Vue owns selection, rendering and clearly labeled replay controls. Browser never accesses SQLite directly.
- Use Yahoo's real WebSocket via yfinance. Never substitute generated prices or polling and claim live streaming. Record real-provider evidence separately from mocks. No credentials required for the present feed; never commit .env or secrets.
- Preserve SQLite records. Never delete/reseed to improve evidence. Ignore .venv, node_modules, build output and databases. Use CREATE TABLE IF NOT EXISTS at startup.
- Timestamped quote identity is not an exchange trade ID. Keep exact duplicate suppression, append-only revisions, source-time ordering and receipt-order replay. Preserve provisional/elapsed candle state. Document sample and volume limitations honestly.
- New dependencies require student's approval. Vue/Vite, Lightweight Charts, FastAPI/uvicorn and yfinance were approved November 10, 2026. Playwright and its Chromium test browser were approved November 16, 2026. Dependencies installed transitively are locked in backend/requirements.txt and frontend/package-lock.json.
- Before committing, obtain fresh student VS Code review and browser acceptance, run backend tests and frontend production build, and review docs/evidence against actual results. Do not claim student review, GitHub publication, video accessibility, Canvas upload or class presentation without confirmation.
- Keep report.md for the current submission, maintain README, docs/design.md, AI-USE.md and evidence/evidence-log.md. Submit only report.md to Canvas; repository URL, submitted commit and an accessible 30–60 second video are required.

## Part 4.2

- Preserve docs/assignment-4-part-1-report-archive.md and existing market records. Root report.md is the Part 4.2 report, written in the student's first-person voice with accurate AI disclosure. The Part 4.1 video is not evidence of new Part 4.2 features.
- Backend owns strategy decisions, paper accounts, orders/fills, money calculations and backtests. Record config, source, receipt cutoff and assumptions with each run. Use only prices known at decision time and a later eligible quote to fill. Exclude unfinished bars; never rewrite an executed decision after late data.
- Compare SMA batch/incremental calculations against pandas (already installed) and fixed known examples. Test accounting, warmup, equality/crossovers, late revisions, future-prefix independence and restart idempotency. Keep synthetic practice and actual Yahoo evidence labeled separately.
- Keep repeatable browser tests and CI on push/pull_request. Do not claim a remote Actions run passed until verified. Student approval of the completed Part 4.1 does not establish personal review of the new Part 4.2 interface; prepare the work before requesting that review.
