# Part 4.2 design: indicators, execution and accounting

## Responsibilities and flow

The existing Yahoo → observation journal → market chart path is preserved. FastAPI owns strategy inputs, paper-account lifecycle, orders/fills, money arithmetic and backtests. Vue owns controls, charts, account summaries and the order table. `backend/strategy.py` is the deterministic receipt-time engine; `backend/trading.py` persists state and exposes `/api/trading/runs`, `/runs/{id}` and `/runs/{id}/stop`. Only local simulated activity exists; there are no broker credentials or trading endpoints.

A single account worker runs every second. Each running account reads observations after its saved sequence cursor, processes up to 5,000 receipts per pass, and atomically saves the cursor, strategy state, orders and fills. When caught up, it can close a candle according to the local clock even without a new quote. Restart processes missed receipts in order; it does not execute the same receipt twice. A process lock serializes account mutation in the supported single-worker deployment. The original journal and market candles are never deleted or reseeded.

## Indicators and decisions

Defaults are SMA(3) and SMA(8) on observed, completed one-minute closes. Short windows make the classroom's limited recorded history usable; they are not optimized for profit. Users can choose 2 ≤ fast < slow ≤ 200. No value exists until a full window is available. Missing minutes stay missing: a window counts observed candles, not consecutive elapsed minutes.

The backend incremental calculation keeps a rolling queue and sum. A separate batch implementation uses independent slices and `math.fsum`. Tests compare both to the already-installed pandas `Series.rolling(window,min_periods=window).mean()`. A checked-in pandas fixture independently checks the browser's overlays and crossover markers.

A strictly negative fast-minus-slow relationship followed by a strictly positive one is a buy crossover; the opposite is a sell crossover. Equality keeps the most recent strict side, so touching and moving back to the same side does not emit a duplicate signal. Equality tolerance is max(1e-10 absolute, 1e-12 relative). The first valid pair establishes a side without placing an order. Current unfinished candles cannot create signals.

For each received quote, the strategy first closes elapsed bars using data from **previous receipts**, then considers a fill on the arriving quote, then updates its open-bar inputs and account mark. Source timestamps later than the available receipt clock are ignored by the strategy. Receipt time is monotonicized with `max(previous_clock, received_ms)`; the journal sequence breaks timing ties. A quote received exactly at a close boundary is processed after that closure.

Once a strategy candle is closed, its decision values are frozen. Later corrections to that minute remain in the market journal and can correct the upper chart, but do not rewrite orders or frozen indicators. This deliberately differs from calculating a backtest over today's final corrected candles. The lower run chart makes the actual frozen values visible. Late receipts and ignored future-dated quotes are counted in the run response.

## Execution assumptions

Each account has one symbol and is long or flat. A buy enters a fixed quantity only when flat; a sell closes the entire position. Other crosses are recorded as skipped. There is no shorting, leverage, pyramiding or partial fill. An opposite crossover cancels an older pending order before queuing its eligible replacement.

An order stores decision time, signal candle time and the last known receipt sequence. It fills only on a receipt with a larger sequence and source time at or after the signal candle's end. Thus the signal candle's closing price cannot fill its own decision. The incoming quote can share a wall-clock millisecond with the decision; it is still a later receipt. This is a sampled quote execution model, not an exchange order book.

Buy fill = observed price × (1 + slippage_bps / 10,000); sell fill = observed price × (1 − slippage_bps / 10,000). Fill price is rounded half-up to six decimals. Gross = quantity × fill price, rounded half-up to cents. Each executed side pays the configured fixed fee. Defaults: $10,000, one unit, $1 fee, 5 bps; BTC defaults to 0.01 units when selected. Dollar arithmetic uses Decimal and values are stored as decimal strings.

A buy that cannot cover gross plus fee is rejected without changing cash or charging a fee. An exit that would make cash negative after its fee is also rejected and retains the position. End-of-data pending orders are cancelled; no price or final sale is fabricated. A stopped paper account cancels pending orders and preserves a frozen account, including its open position.

## Accounting

- Entry cost basis = buy gross + entry fee. Cash decreases by that amount.
- Position value = units × latest known source-ordered mark, rounded to cents. A late older quote cannot move the mark backwards.
- Unrealized P/L = position value − entry cost basis. A hypothetical exit fee is not included.
- Realized P/L at exit = sell gross − exit fee − entry cost basis. Cash receives sell gross − exit fee.
- Equity = cash + position value. Total P/L = equity − initial cash = realized + unrealized P/L.
- Return = total P/L / initial cash. Maximum drawdown is the largest percentage drop from a prior observed equity peak, computed over the entire processed stream even though the plot shows only 500 points.

Known example: $1,000 cash, 2 units, $1 fee per side, 10 bps slippage. A $100 buy quote fills at $100.10: gross $200.20, basis $201.20, cash $798.80. A $110 mark gives $18.80 unrealized P/L. A $110 sell quote fills at $109.89: gross $219.78, net proceeds $218.78, final cash $1,017.58 and realized P/L $17.58. Automated checks assert these independently calculated amounts.

## Backtests and reproducibility

Saved-Yahoo backtests use the latest at most 50,000 journal receipts for one symbol, in sequence order, including revisions only when they arrive. Each run records the count, first sequence, cutoff sequence, receipt date range, source and immutable settings. A truncated window is labeled. The final available receipt defines the horizon; its still-open candle is excluded. Open positions are marked, not forced closed. The original journal retains the underlying inputs.

Paper accounts use the same engine. Historical warmup establishes indicators but cannot trade. Only receipts arriving after account creation can result in new fills. Backtests close bars when a subsequent receipt advances the historical clock; live accounts additionally have a wall-clock timer. In sparse feeds this can give different decision times, although both use only available data. This is an explicit limitation, not claimed exact reproduction of every live schedule.

Synthetic practice is a fixed fixture in `backend/tests/fixtures/practice-quotes.json`. Invented AAPL-labeled prices make crossovers and accounting reproducible without a network. They never enter the market observations or candles tables. A practice result is not a historical market return.

## Additional SQLite tables

All are created with `CREATE TABLE IF NOT EXISTS` in the existing ignored market database.

| Table | Stored data |
|---|---|
| `simulation_runs` | UUID primary key; mode, status, symbol, source, creation timestamp; immutable configuration and input metadata JSON; durable engine state JSON (cursor, open bars, frozen indicator window, balances, marks, signals and plot samples). |
| `simulated_orders` | Composite key (run_id,id); side, status, decision milliseconds, decision sequence and full order JSON including signal time, quantity, fill reference and reason. Pending orders can become filled, rejected or cancelled. |
| `simulated_fills` | Composite key (run_id,id); order ID, receipt sequence, price/quantity/fee decimal strings and full fill JSON with source/receipt timestamps, gross, realized P/L and resulting cash/position. Fills are insert-only. |

An account update stores the durable engine state and normalized ledger in one transaction. No reset/delete endpoint is provided. The latest 50 runs are listed in the UI; older runs remain in SQLite. All orders/fills remain accessible for a selected run, while price/equity plots show at most 500 points.

## Limits and references

Short, sampled local histories are incomplete and do not establish future performance. There is no exchange spread, liquidity, partial-fill, market-impact, tax, interest or corporate-action model. Network gaps and quote latency can change fills. Windows span observed bars across session gaps. Large numbers of simultaneous accounts or unlimited journal growth are not a production workload this local prototype has been tuned for. Feed controls and account endpoints are localhost-only and unauthenticated.

References consulted November 16, 2026: [pandas windowing](https://pandas.pydata.org/docs/user_guide/window.html), [pandas Series.rolling](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.rolling.html), [TradingView SMA definition](https://www.tradingview.com/support/solutions/43000696841-simple-moving-average/), [Playwright testing](https://playwright.dev/docs/intro), [GitHub workflow triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

## Chart presentation

Both candlestick charts begin with the latest 60 loaded candles; the user can show all loaded history or zoom/pan manually. The full loaded series still supplies the indicators. Smaller, text-free arrows identify every crossover, with an upward/downward legend and an explicit signal-versus-fill distinction. SMA lines are thin enough to leave candle bodies and wicks visible. This view change does not alter the strategy, observation history or accounting.
