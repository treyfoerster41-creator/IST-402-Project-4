# Part 4.1 design

## Data flow and responsibilities

Yahoo Finance pricing stream → yfinance AsyncWebSocket → FastAPI validator → SQLite observation transaction → deterministic one-minute bar builder → persisted candle materialization → FastAPI /api/ws/{symbol} → Vue → TradingView Lightweight Charts candlestick and volume series.

One upstream connection subscribes to AAPL, MSFT and BTC-USD for the lifetime of the backend. Vue receives a bounded complete chart snapshot every second, not a new fabricated price. Upstream messages are persisted even without a browser. A displayed price only changes when a provider quote or stored replay receipt changes it. Browser connection retries every two seconds; backend failures retry every five seconds. Quote validation rejects unsupported symbols, nonpositive/nonfinite prices, invalid source timestamps and negative volume. Provider failures become sanitized status messages.

FastAPI /api/observations/{symbol} retrieves up to 10,000 latest journal rows in local receipt sequence. Vue reconstructs a selected receipt prefix for replay; no future revisions are applied, and completion uses the last reached receipt time. A request token discards stale replay responses after instrument/mode changes. Replay is accelerated (150 ms/receipt), not a backtest. No strategies or accounting exist in this part. POST /api/feed/pause and /resume deliberately interrupt/resume the upstream feed for classroom failure evidence. Not suitable for a public deployment.

## SQLite schema

`observations`: seq INTEGER PRIMARY KEY AUTOINCREMENT; identity TEXT; revision INTEGER; symbol TEXT; source_ms INTEGER; received_ms INTEGER; price REAL; day_volume INTEGER NULL; digest TEXT; payload TEXT. All except day_volume are NOT NULL. Unique(identity,revision) and unique(identity,digest); index(symbol,seq). Payload is canonical JSON, digest is SHA-256. All times are Unix UTC milliseconds. seq is authoritative local receipt order even if wall clocks move backwards. No provider trade ID is supplied: identity is `yahoo:{symbol}:{source_ms}`, explicitly a quote slot. Multiple same-millisecond quotes may be treated as revisions; this is not lossless trade-tape reconstruction.

`candles`: composite primary key(symbol,time); open/high/low/close REAL; volume INTEGER; volume_known INTEGER; complete INTEGER; revision INTEGER; updated_ms INTEGER. time is minute-open Unix UTC seconds; other times are milliseconds. Materialized current bars persist a completeness flag and revision counter. Journal observations preserve the inputs needed to reconstruct earlier versions. Upserts occur only when bar fields change. Ingestion materializes bars and browser snapshots advance time-based closure. Two transactions are used: a crash after journaling but before materialization is recoverable by the startup reconstruction from journal rows. Ingestion rebuilds the affected source minute and the next sample’s minute (whose volume delta may change), including each minute’s true predecessor. Database connections close explicitly after their transaction. No destructive schema reset or seed occurs at startup; WAL is enabled.

## Ordering, revisions and completeness

- Exact duplicate canonical payload for an identity: ignored; no extra journal row, no repeated volume. Original receipt remains. Repeat delivery counts are not retained.
- Different payload for an existing identity: append revision MAX+1. Prior revisions remain. Latest receipt revision wins for that quote slot. A repeat of an earlier already-known payload is deduplicated rather than reverting the latest revision.
- Out-of-order timestamp: append at its arrival sequence; rebuild bars by source timestamp, with seq as tie-breaker. Earlier-minute OHLCV can change. Replay sorts only the quote slots known at that receipt prefix.
- One minute uses source timestamps: open/close are first/last source samples; high/low extrema. Missing minutes are absent. Current bar is incomplete; complete means interval ended according to server clock, not final or exchange-confirmed. Late data can revise complete bars.
- Volume: sum nonnegative daily counter changes for source-ordered adjacent known samples from the same UTC date, credited to the later sample's minute. Initial/missing/reset counts contribute nothing and remain explicitly unknown if no valid delta exists. UTC reset boundaries are conservative and may not match exchange sessions. Disconnections can assign multi-minute volume to a later sample. No claim of official per-minute exchange volume.

Replay is bounded to the latest 10,000 revisions; it can omit earlier revisions and the baseline before its first retained sample. The live chart independently reads the latest 500 persisted candles. Candle materialization always uses full source-minute history and its predecessor, so the replay/display limit cannot corrupt historical opens or volume. The SQLite journal itself has no automatic retention deletion. Selected-symbol age is independent of all-symbol connection health; stale is based on the selected symbol's most recent receipt. Source age can reveal old quotes received recently. The client clock is used for age display, so clock skew can affect the displayed age.

## Verification and remaining scope

Tests use temporary SQLite files and synthetic labeled quotes. They cover deduplication, revisions, source ordering/OHLC, volume reset, invalid values, persistence through reinitialization, cutoff queries, persisted candle completion and sanitized mocked failure. Real Yahoo and browser checks are separate in evidence. Part 4.2 indicators/trading/backtesting and Part 4.3 AI/audio are not implemented.

The Yahoo adapter follows [yfinance's asynchronous streaming API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.AsyncWebSocket.html). Chart choice: [Lightweight Charts](https://github.com/tradingview/lightweight-charts) provides financial candles, aligned volume, zoom/pan, resizing and visible attribution; Vue keeps rendering state separate from backend persistence.


## Reviewed adapter and regression checks

The yfinance dependency is pinned to 1.8.0. `listen_quotes` uses its subscribed socket and protobuf decoder; those two internal fields are isolated in that adapter. A clean upstream close raises to the supervisor so it creates a fresh client rather than repeatedly iterating a closed socket. Dependency upgrades must recheck the adapter. Exceptions propagate to the supervisor and the browser receives a sanitized failure message.

Twelve backend tests and five frontend replay tests cover the original behaviors plus a journal exceeding 10,000 receipts, the next-minute volume correction caused by late data, recovery after a materialization gap, clean upstream closure, selected-symbol staleness and replay-time completion. The browser’s latest-minute OHLC/volume/completion text provides an accessible summary of the canvas chart. Real-provider checks remain distinct from synthetic tests.

BTC-USD volume is deliberately unknown because its provider counter semantics have not been validated as cumulative session volume. Equity volume remains a qualified observed counter difference; raw provider fields are preserved.
