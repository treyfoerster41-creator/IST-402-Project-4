# Assignment 4, Part 1 — Market Data and the Dashboard

**Student:** Trey Foerster

**Date:** November 10, 2026

**Status:** Working local implementation; student VS Code/browser review accepted; GitHub published and clean checkout verified; demonstration video link pending.

## Completed

Signal Desk is a separate Vue/FastAPI/SQLite application. It subscribes to Yahoo Finance's live WebSocket through yfinance, stores real observation revisions, and sends one-minute sampled candlesticks and observed cumulative-volume changes to the browser through a backend WebSocket. Instruments are AAPL, MSFT and BTC-USD. The interface exposes source, source/receipt age, feed health, record count and the selected observation's identity/revision.

Recorded receipt-order replay includes play/pause and scrubbing. Deliberately pausing the upstream feed shows unavailable while SQLite records remain available. Restart and refresh preserve observations. The application makes no trades or financial recommendations.

## Decisions and correctness

The backend owns data validation, storage and aggregation; Vue owns display and replay selection. SQLite keeps append-only observation revisions and materialized candles with completeness flags. Exact repeated payloads are deduplicated; changed payloads at the same symbol/source timestamp append revisions. Late observations rebuild bars in source-time order. Replay uses only the selected receipt prefix, so later revisions are not applied early.

Yahoo quote timestamps are not unique exchange trade IDs. These candles use observed samples rather than a complete trade tape. Volume shows nonnegative changes in cumulative daily volume and may span missed intervals; unknown first/reset/missing values are omitted. Elapsed candles can still be revised. The live chart shows up to 500 persisted candles; replay is capped at 10,000 latest revisions per instrument. Stored candle corrections use full minute history, and the database preserves earlier records.

## Verification

Agent-run checks on November 10, 2026: 12 backend tests, 5 frontend replay tests and the Vue production build passed. Tests cover duplicates, revisions, out-of-order arrival/OHLC, volume reset, invalid prices, database persistence, receipt cutoff, stored candle completion, invalid symbols, sanitized mocked provider failure, clean stream closure, replay-time completion and a regression with more than 10,000 receipts. Live Yahoo observations separately reached the backend WebSocket, SQLite and rendered chart. Browser outage/replay and persistence checks are documented in the [evidence log](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/evidence/evidence-log.md). These checks were agent-run. On November 10, 2026, the student confirmed personal VS Code review and browser acceptance and authorized committing.

A failed initial connection exposed a Python CA-bundle configuration issue. Using the installed certifi trust bundle preserved certificate verification and allowed live data to arrive. The relevant generated code is backend/main.py's SSL_CERT_FILE configuration and feed lifecycle. This was an environment fix. A subsequent code review found that truncating the input window could change a historical candle’s opening price; materialization now reads the full affected minute plus its predecessor. A regression test with 10,001 saved receipts verifies that the original open/high survive.

## Supporting material

- [README and startup](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/README.md)
- [Architecture, SQLite schema and limitations](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/docs/design.md)
- [Verification and process evidence](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/evidence/evidence-log.md)
- [AI tools and generated-code disclosure](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/AI-USE.md)
- [Video and student review checklist](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/docs/demo-checklist.md)

## Submission links — add the video before uploading

- **GitHub repository URL:** [IST-402-Project-4](https://github.com/treyfoerster41-creator/IST-402-Project-4).
- **Submitted application commit:** [`b8f7845`](https://github.com/treyfoerster41-creator/IST-402-Project-4/commit/b8f78450598fa012bca6b7da37510712285dd0a1) — reviewed application code; subsequent documentation updates do not change application behavior.
- **Single 30–60 second demonstration video:** PENDING — student recording/link required.
- **Repository access:** verified by an agent-run clone without a credential helper or login prompt. **Video access:** pending the student’s link and access confirmation.

Only this report.md is uploaded to Canvas. Source remains in the linked GitHub repository. Student review/acceptance is confirmed; no Canvas upload, private-window access check or class demonstration is claimed. An independent clone of the published application commit passed all 17 tests, the production build and backend startup with automatic SQLite initialization. This startup check began with zero observations and does not replace the separate live-provider evidence.

BTC-USD volume is deliberately unknown because its provider counter semantics have not been validated as cumulative session volume. Equity volume remains a qualified observed counter difference; raw provider fields are preserved.
