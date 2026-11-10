# Signal Desk — Assignment 4.1

Local Vue/FastAPI/SQLite market dashboard. Receives Yahoo Finance WebSocket quotes through yfinance, stores observation revisions, and pushes sampled one-minute candlesticks and observed volume to Vue through a second WebSocket. Includes receipt-order replay and deliberate feed outage/reconnect controls. No trading or model integration in Part 4.1.

## Start from a clean checkout

Verified environment: Python 3.14 and Node/npm. No API key or .env is required. All commands below run from the repository root unless noted.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8004
```

In a second terminal:

```sh
npm --prefix frontend run dev
```

Open http://127.0.0.1:5174/. Vite proxies /api (including WebSockets) to port 8004. Keep both processes running. Use one backend worker: each worker would otherwise open a separate upstream subscription. Server binds to localhost only; feed controls are unauthenticated local demonstration controls, not deployment endpoints.

SQLite initializes automatically at backend/data/market.db using idempotent schema creation. There is no starter-data seed and no CSV dependency. Database and sidecar files are ignored. Reopening the app or restarting the backend preserves observations; do not delete the database. The backend uses the installed certifi CA bundle when SSL_CERT_FILE is unset; TLS certificate verification stays enabled.

## Use

Choose AAPL, MSFT or BTC-USD. Source age measures elapsed time since the selected quote's source timestamp; receipt age measures time since this server received it. A live label is not proof every instrument is trading: inspect source age. Status distinguishes connecting, connected/waiting, live, stale and unavailable; browser disconnection is separate. AAPL/MSFT depend on market hours and provider timing; BTC-USD may update outside equity hours. No latency guarantee is made.

Recorded replay loads up to 10,000 latest observation revisions for the selected instrument, starts at the first retained receipt and applies revisions only when their receipt is reached. Play advances one receipt every 150 ms (accelerated receipt-order replay, not original timing). Use the slider to scrub. No records means an honest empty state; there is no synthetic fallback. Live collection continues while replay is selected. Return to Live stream for the current view.

Simulate feed outage pauses the real upstream connection. Status becomes unavailable; existing chart records remain. Recorded replay still works. Reconnect Yahoo resumes the connection. This deliberate simulation is labeled separately from a natural provider failure.

## Verify

```sh
.venv/bin/python -m unittest discover -s backend/tests -v
npm --prefix frontend test
npm --prefix frontend run build
```

See [design](docs/design.md), [evidence](evidence/evidence-log.md), [demo checklist](docs/demo-checklist.md), [AI disclosure](AI-USE.md) and [submission report](report.md). Live Yahoo requires network access and provider availability. Mock tests alone do not prove live success. Browser refresh and backend restart checks are documented separately. A fresh independent checkout is still pending until a repository and submitted commit exist.

## Data limitations

These are sample-derived candles, not official Yahoo OHLCV bars or a complete exchange trade tape. Daily cumulative volume differences are attributed to the interval of the later sample; missed intervals cannot be reconstructed exactly. First samples, missing values and counter resets have unknown volume and are omitted from the histogram. Gaps are not filled. Elapsed candles remain revisable by late data. The journal retains all stored rows. The live chart shows the latest 500 stored candles; the count and replay use the latest 10,000 revisions per instrument. Materialization uses the full journal for each affected minute, including its predecessor, so display limits cannot change stored candle values. Earlier records remain in SQLite. No investment recommendations are provided.

References: [yfinance streaming](https://ranaroussi.github.io/yfinance/reference/yfinance.websocket.html), [Lightweight Charts](https://github.com/tradingview/lightweight-charts), [Yahoo Finance](https://finance.yahoo.com/). Yahoo access and permissible uses remain subject to provider terms; this is a classroom prototype.

BTC-USD volume is deliberately unknown because its provider counter semantics have not been validated as cumulative session volume. Equity volume remains a qualified observed counter difference; raw provider fields are preserved.
