# One 45–60 second video

Student VS Code/browser review and acceptance were confirmed November 10, 2026.

Before recording, open the dashboard with AAPL selected and Live stream active. Open backend/data/market.db in the already-installed DB Browser for SQLite; prepare Browse Data → observations. Do not edit or delete records. Record when AAPL shows recent live updates so both price and equity volume can be demonstrated.

1. **0–15 seconds:** Show AAPL candles, volume, LIVE status, source/receipt age and stored record count. Say: “Yahoo Finance streams quotes to my FastAPI backend, which stores them in SQLite and sends chart updates to Vue over WebSockets.”
2. **15–25 seconds:** Briefly switch to SQLite observations and show identity, revision, source_ms and received_ms. Say: “I preserve source and receipt times. Exact duplicates are ignored and changed observations keep revisions.”
3. **25–35 seconds:** Return to the dashboard and click Simulate feed outage. Wait for unavailable. Say: “This pauses Yahoo updates; the saved data stays.”
4. **35–45 seconds:** Click Recorded replay, then Play. Say: “Replay uses real saved observations from SQLite in arrival order, including revisions.”
5. **45–60 seconds:** Click Reconnect Yahoo and Live stream. Show live status returning. Say: “Candles use sampled quotes. I tested duplicates, revisions and out-of-order arrivals.”

Keep the whole recording under one minute. If reconnection is slow, wait for it and record another take. Upload the single video to an instructor-accessible service, confirm access and duration, and provide its URL. No video/access/Canvas submission is claimed until verified. Upload only report.md to Canvas after adding the repository URL, submitted commit and video link.

## Finding the saved table

Open DB Browser for SQLite (already installed on the student’s Mac), choose Open Database, and select market.db inside IST 402 → Assignment 4 → backend → data. Select the Browse Data tab, then observations in the table dropdown. Each row is a saved Yahoo update. identity identifies a timestamped quote slot, revision identifies a changed version, source_ms is the provider’s timestamp, and received_ms is the backend’s receipt timestamp (Unix UTC milliseconds). Showing these rows is enough for the brief persistence segment; no edits are needed.
