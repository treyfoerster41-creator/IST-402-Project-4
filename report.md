# Assignment 4, Part 1 - Market Data and the Dashboard

**Trey Foerster**

November 10, 2026

## What I completed

For Part 4.1, I built Signal Desk, a market dashboard that displays live data from Yahoo Finance. I used Vue for the frontend, FastAPI for the backend, SQLite for storage, and Lightweight Charts for the candlestick and volume charts. I used Codex to help with implementation, testing, and documentation, and I reviewed the code in VS Code and the working application in the browser.

The dashboard supports AAPL, MSFT, and BTC-USD. Yahoo quotes reach the backend through yfinance's WebSocket connection, are saved in SQLite, and are sent to the browser over another WebSocket. The page shows the data source, how old the source and received data are, the feed status, and the number of stored observations.

I also included recorded replay with play, pause, and a slider. Replay uses saved Yahoo observations, so it can work when the live feed is unavailable. The **Simulate feed outage** button pauses the Yahoo connection and displays an unavailable status. **Reconnect Yahoo** starts the connection again. Saved records stay in the database through an outage, browser refresh, or server restart.

## How I handled the data

I kept the data processing in the backend and the chart controls in Vue. The browser requests data from the backend and never opens SQLite directly. The backend creates the database tables at startup. Setup instructions are in the README, and the current Yahoo feed does not require credentials.

Each saved observation includes its identity, source time, receipt time, and revision. The identity uses the symbol and Yahoo timestamp; it is not an exchange trade ID. Exact duplicate payloads are ignored. If a payload changes for the same identity, the backend saves a new revision and keeps the earlier version. When an observation arrives late, the affected candles are recalculated using source-time order.

Replay follows the order observations were received. It only uses the records available at the selected replay point, so a later correction does not appear before it actually arrived. Candles also have a completion flag: the current minute is provisional, while an elapsed minute is marked complete but can still be revised if late data arrives.

## Testing and fixes

Codex ran **12 backend tests and 5 frontend replay tests**, and all 17 passed. The frontend production build also passed. These checks covered duplicate and revised observations, out-of-order arrivals, volume resets, persistence, replay timing, and feed failures. A separate live check confirmed that actual Yahoo observations reached the backend, SQLite, and the chart. The outage, replay, refresh, and restart results are recorded in the evidence log.

Two fixes were particularly useful. The initial Yahoo connection failed because Python could not find its certificate trust bundle. Configuring the installed certifi bundle fixed the connection while keeping certificate verification enabled. Review also caught a problem where limiting the chart's input history could change an older candle's opening price. Candle calculations now use the full affected minute and its preceding observation. A test with 10,001 saved receipts confirms that the original open and high are preserved.

A fresh clone of the GitHub repository also passed the tests, build, and startup check, including automatic SQLite initialization. I personally reviewed the code and browser application, recorded the demo, and confirmed that my Kaltura link works in a private browser.

## Remaining limitations

The candles are built from sampled Yahoo quotes, so they are not official exchange OHLCV bars. Equity volume comes from changes in the reported cumulative volume and can span missed intervals. Missing values and counter resets are treated as unknown. BTC-USD volume is left unknown because its counter behavior has not been validated.

The live chart displays up to 500 stored candles, and replay loads up to the latest 10,000 revisions per instrument. Earlier records remain in SQLite. This part focuses on collecting, displaying, and replaying market data; trading and the later assignment features are not implemented yet.

## Repository and demo

- **GitHub:** [IST-402-Project-4](https://github.com/treyfoerster41-creator/IST-402-Project-4)
- **Application commit:** [`b8f7845`](https://github.com/treyfoerster41-creator/IST-402-Project-4/commit/b8f78450598fa012bca6b7da37510712285dd0a1). This identifies the reviewed application; later commits update the documentation.
- **My demo video:** [IST 402 - Assignment 4.1 Demo](https://psu.mediaspace.kaltura.com/media/t/1_4ntm2z5s), 1 minute 25 seconds. I verified access in a private browser.

The repository was also successfully cloned without signing in. I am submitting this report to Canvas, with the source code and supporting files kept in GitHub.

## Supporting documents

- [README and startup instructions](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/README.md)
- [Design notes, data flow, and SQLite schema](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/docs/design.md)
- [Test results and live evidence](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/evidence/evidence-log.md)
- [Project agent instructions](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/AGENTS.md)
- [AI-use disclosure](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part1/AI-USE.md)
