# Assignment 4 — Signal Desk

Use Vue, FastAPI and SQLite on localhost. Parts 4.1–4.3 are cumulative. Current scope is Part 4.1 only: live Yahoo streaming, sampled candlesticks/volume, persistence, replay, visible provenance and failures. All future trading must be simulated.

- Backend owns Yahoo integration, validation, append-only observation revisions, candle aggregation, SQLite initialization and API/WebSocket routes. Vue owns selection, rendering and clearly labeled replay controls. Browser never accesses SQLite directly.
- Use Yahoo's real WebSocket via yfinance. Never substitute generated prices or polling and claim live streaming. Record real-provider evidence separately from mocks. No credentials required for the present feed; never commit .env or secrets.
- Preserve SQLite records. Never delete/reseed to improve evidence. Ignore .venv, node_modules, build output and databases. Use CREATE TABLE IF NOT EXISTS at startup.
- Timestamped quote identity is not an exchange trade ID. Keep exact duplicate suppression, append-only revisions, source-time ordering and receipt-order replay. Preserve provisional/elapsed candle state. Document sample and volume limitations honestly.
- New dependencies require student's approval. Vue/Vite, Lightweight Charts, FastAPI/uvicorn and yfinance were approved November 10, 2026. Dependencies installed transitively are locked in backend/requirements.txt and frontend/package-lock.json.
- Before committing, obtain fresh student VS Code review and browser acceptance, run backend tests and frontend production build, and review docs/evidence against actual results. Do not claim student review, GitHub publication, video accessibility, Canvas upload or class presentation without confirmation.
- Keep report.md for the current submission, maintain README, docs/design.md, AI-USE.md and evidence/evidence-log.md. Submit only report.md to Canvas; repository URL, submitted commit and an accessible 30–60 second video are required.
