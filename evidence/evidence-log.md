# Part 4.1 evidence — November 10, 2026

Technical checks below are **agent-run observations**. Student review and video-access confirmation are recorded separately from those checks; class demonstration and Canvas submission are not claimed. Local times are America/New_York (EST); JSON timestamps are UTC. Synthetic automated tests use temporary databases; the working database was preserved.

## Curated process trail

| Intended change / instruction excerpt | Resulting code or artifact | Verification and observed result | Decision / uncertainty |
|---|---|---|---|
| “Connect to Yahoo Finance … Use WebSockets … source, age, and feed status visible.” | backend/main.py, frontend/src/App.vue | Actual Yahoo observations arrived through backend WebSocket and rendered as candles/volume. At about 13:48 EST the browser showed AAPL LIVE, source age 0–2 seconds, and changing SQLite receipt counts. | Source/receipt age remain visible; no guaranteed real-time latency is claimed. |
| “Preserve observation identity, source and receipt times, revisions … duplicate, revised, and out-of-order.” | backend/store.py and backend/tests/test_store.py | Dedup, revision history, chronological OHLC, receipt cutoff and late-volume correction tests passed. | Timestamped quote-slot identity is disclosed; Yahoo supplies no exchange trade ID. |
| Initial live connection failed | backend/main.py CA-bundle setup | SSL certificate verification failed because Python could not locate its trust bundle. Configuring installed certifi with verification enabled allowed live quotes to arrive. | Environment fix verified with real Yahoo; failure was not hidden behind synthetic data. |
| “go back make sure all ist gut … dont take too too long” | affected-minute materialization, replay request token, listen_quotes adapter | Review found the bounded-record window could alter stored opens. A 10,001-record synthetic regression now preserves the original open/high. Tests also cover clean close and replay completion at its historical receipt time. | Keep display bounds separate from authoritative stored-bar calculations; keep changes inside 4.1. |
| Code comprehension / ownership | readable Vue script, replay.js comments, docs/design.md, AI-USE.md | Architecture/schema and generated-code decisions documented. | Student subsequently confirmed personal VS Code review and browser acceptance. |

## Expected versus observed

| Check | Expected | Observed |
|---|---|---|
| Backend suite | Deterministic handling and persistence; no live-provider dependency | **12 tests passed** using temporary SQLite databases and mocked failure. |
| Frontend replay suite | Receipt prefixes exclude future revisions; late samples order by source time; empty state and historical completion | **5 tests passed** using Node's built-in test runner. |
| Production build | Vue and chart library compile | **Passed**, Vite 6.4.6. |
| Live source → backend → database → chart | Actual Yahoo quotes saved and streamed to rendered candles and aligned volume | **Observed** AAPL price/candle/volume and record count change. [Live status](live-status.png), [chart](live-chart.png), [raw real sample](live-yahoo-sample.json). |
| Unavailable feed | Deliberate pause closes upstream; status unavailable and records remain | **Observed** labeled unavailable state and unchanged AAPL record count (191) across successive backend snapshots. [Failure screenshot](unavailable-feed.png), [backend proof](backend-verification.json). |
| Replay during outage | Stored real receipts replay while upstream is paused | **Observed** playback from receipt #2, AAPL $347.95 with unknown first volume, to later receipts/prices/volume. Header says RECORDED REPLAY. [Replay screenshot](recorded-replay.png). |
| Browser refresh | Persisted records reload; pause remains a server state | **Observed** refreshed page retained 64 AAPL revisions during the earlier pause and displayed unavailable. |
| Server restart | Records survive; original payload identity/digest remain | **Observed** restarts without reseeding. Original receipt #2 digest matched saved live sample after final restart; 426 total revisions were present at 13:49 EST (191 AAPL, 39 BTC-USD, 196 MSFT). Counts subsequently grow with live use. |
| Completion | Current minute provisional, elapsed bars close but remain revisable | **Observed** latest-minute text changed to elapsed/revisable during pause. SQLite complete=1 verified on older candle. Regression tests verify stored flags and revision increments. |
| Reconnect and symbol switch | Live resumes; selected symbol and chart agree | **Observed** resumed AAPL live, then MSFT live with corresponding MSFT identity/candles. |
| Empty history | No synthetic fallback | Empty database/state validated by tests and observed in the initial browser before the first live connection succeeded. |

## Limits of this evidence

Screenshots are snapshots, not the required 30–60 second video. Live data comes from sampled Yahoo quotes; missing first/reset volume is unknown and interval volume is an observed counter difference, not official exchange OHLCV. Replay is accelerated receipt-order playback, not a backtest. Tests use synthetic fixed inputs and do not establish live provider availability. Backend failure tests do not establish behavior of every possible Yahoo outage.

Student VS Code review/browser acceptance was confirmed on November 10, 2026. GitHub publication and an independent checkout check are now complete (details below). The video link and access confirmation are now recorded below. Its 1:25 duration exceeds the required 30–60 seconds. Canvas upload remains pending. See [demo checklist](../docs/demo-checklist.md) and [report](../report.md).

Final check logs: [backend tests](backend-tests.txt), [replay tests](frontend-tests.txt), [production build](frontend-build.txt). Additional regression verifies BTC volume remains unknown rather than assuming counter semantics.

## Student acceptance

November 10, 2026: the student stated, “reviewed vscode and accept both, so they can commit,” confirming personal VS Code review and browser acceptance and authorizing the local commit. This does not establish GitHub publication or video/Canvas completion.

Post-acceptance checks: 12 backend tests and 5 replay tests passed; production build passed. Combined application check returned saved AAPL candles over the backend WebSocket with feed status live before the authorized commit.

## GitHub publication and independent checkout

November 10, 2026: pushed reviewed application commit `b8f78450598fa012bca6b7da37510712285dd0a1` to [IST-402-Project-4](https://github.com/treyfoerster41-creator/IST-402-Project-4), branch `codex/assignment4-part1`. A clone with credential helpers disabled and interactive authentication disabled succeeded, establishing public Git read access at verification time; this was not a claimed student private-window check.

The independent checkout installed the already-approved locked dependencies. Expected: all tests/build succeed and a clean startup creates its own database. Observed: 12 backend tests, 5 replay tests and production build passed; the backend WebSocket returned AAPL with zero observations and connecting status, and SQLite schema existed. The original working database was untouched. The checkout remained Git-clean after testing. This proves reproducible startup, not a second live Yahoo success.

Evidence: [verification record](clean-checkout-verification.json), [backend](clean-backend-tests.txt), [replay](clean-frontend-tests.txt), [build](clean-frontend-build.txt).

## Student video and access confirmation

November 10, 2026: the student supplied [IST 402 — Assignment 4.1 Demo](https://psu.mediaspace.kaltura.com/media/t/1_4ntm2z5s) and explicitly confirmed that it works in a private browser. An agent browser check also opened the page and started playback without a sign-in prompt; the player displayed **01:25**. This establishes access at verification time, but the recording exceeds the assignment’s 30–60 second requirement.

The corresponding student-provided local recording measured 85.383 seconds. Sampled frames show live AAPL candles/volume and source/receipt ages, symbol switching, recorded replay, a return to live mode, and the SQLite **candles** table with revision/completion fields. This is not a claim that the video shows the observations table’s source and receipt columns; those are documented in the schema, tests and separate live evidence.

A separate 55.023-second MP4 was exported locally by speeding up the complete recording approximately 1.55×, with no footage removed. Native macOS AVFoundation was used without installing packages. Sampled output frames were checked for readable chart/database content. The original recording was preserved. The shortened copy is ignored at evidence/local-video/assignment-4.1-demo-55s.mp4 and has not been verified as the media at the supplied Kaltura link. It is not committed to GitHub.
