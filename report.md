# Assignment 4, Part 2 - Indicators, Simulated Trading, and Backtesting

**Trey Foerster**

November 16, 2026

## What I added

For Part 4.2, I continued working on Signal Desk instead of starting a new application. The Yahoo live feed, candlestick chart, SQLite records, and replay from Part 4.1 are still there. I added two simple moving averages, crossover signals, simulated trading accounts, and backtesting. I used Codex to help implement the changes, run checks, and document the results.

The default averages are SMA(3) and SMA(8). They appear as gold and blue lines, with small arrows showing upward and downward crossovers. I asked for the repeated BUY/SELL labels to be removed because they crowded the chart. The chart now starts with a closer view of the latest 60 candles, with controls to show all loaded history. The legend makes clear that the arrows are signals; actual executions are recorded in Orders & fills. I chose short windows so the strategy can be demonstrated with the recorded data available in this project. The window lengths can be changed in the interface.

The strategy buys a fixed number of units on an upward crossover and sells the position on a downward crossover. Each paper account shows its cash, position, equity, fees, realized and unrealized profit or loss, and maximum drawdown. Orders and fills are listed separately from the chart and saved in SQLite. I can reload a saved run after refreshing the page.

## Decisions and assumptions

I kept the strategy and accounting in FastAPI, with Vue handling the controls and charts. All trades are simulated. The default account starts with $10,000, trades one unit at a time, and applies a $1 fee per fill plus 5 basis points of adverse slippage. It can hold a long position or stay in cash; it cannot short or borrow money.

An unfinished candle does not count toward an SMA or trigger a trade. The first complete pair of averages establishes the initial relationship. After that, a change from one side to the other creates a crossover. If the averages are equal, the strategy keeps the last clear relationship until they separate again.

I also separated a signal from its execution. A signal queues an order, and a later eligible received quote supplies the fill price. The strategy cannot use its own signal candle's close as an immediate fill. Fees are included in cash and profit calculations. Orders are rejected if the account cannot cover the cost, and a backtest does not invent a final trade just to close an open position.

Late data can correct the market chart, but it does not change a trade that already happened in the simulation. The lower chart preserves the candle and indicator values that were actually used for decisions. This avoids letting a later correction make an earlier result look better.

## Backtesting and results

The backtest processes saved Yahoo observations in the order they were received. Revisions become available only when their recorded receipt is reached. Each run saves its settings, source, date range, and receipt cutoff. There is also a clearly labeled synthetic practice dataset for checking behavior without a live feed; those invented prices are kept out of the Yahoo market tables.

In my demo, I changed **Units per buy to 5** and ran the strategy on saved AAPL history. That run used **18,664 recorded observations and 786 completed candles**, covering November 10–16, 2026. With SMA(3)/SMA(8), $10,000 starting cash, a $1 fee per fill, and 5 basis points of slippage, it produced **100 fills** and **$100 in fees**. Final cash and equity were **$9,843.40**, with a **$156.60 realized loss**, **$0 unrealized P/L**, and no open position. The return was **−1.57%**, and maximum drawdown was **1.57%**. The exact settings, receipt cutoff, and sample fills are in my [demo run evidence](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/evidence/part-4.2/demo-run-proof.json).

An earlier one-unit verification run ended at $9,895.51 after 94 fills. That run used an earlier data cutoff, so it is separate from the five-unit run in my video. I kept its [original evidence](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/evidence/part-4.2/run-proof.json) for comparison with the earlier checks.

That result shows how the strategy and execution assumptions behaved on this recorded sample. It does not show that the strategy will work on a different period or predict future returns. A positive result was not the goal; I wanted the calculations and trade history to be explainable.

## Verification

I reviewed the new code in VS Code and tried the Part 4.2 interface in the browser. After reviewing both, I approved committing and publishing this version on November 16, 2026.

Codex ran **27 backend tests, 8 frontend unit tests, and 5 browser tests**. The backend checks compare the batch and incremental SMAs with pandas, verify crossover timing, exclude unfinished candles, and check that future receipts do not rewrite earlier decisions. Other tests cover rejected orders, fees, late revisions, pending orders at the end of a backtest, and persistence without duplicate fills after restart.

One accounting check uses $1,000 starting cash, two units, a $1 fee per side, and 10 basis points of slippage. Buying from a $100 quote leaves $798.80 cash. A $110 mark produces $18.80 unrealized profit. Selling from a $110 quote leaves $1,017.58 cash and $17.58 realized profit. The automated test checks those amounts directly.

The browser tests cover creating a backtest, showing trades and account results, retaining the result after refresh, invalid settings, empty Yahoo history, feed outage, paper-account controls, and a narrow screen layout. An early refresh assertion failed because it compared two different text formats; the displayed amounts were unchanged. The assertion was corrected to compare rendered text consistently, and the browser suite passed.

I added a GitHub Actions workflow to run the backend tests, frontend tests/build, and browser tests on pushes and pull requests. The browser tests use a temporary database and disable Yahoo, keeping them repeatable and separate from the live-provider evidence. After I approved the code and browser interface, the Part 4.2 branch was pushed to GitHub. The [GitHub Actions run](https://github.com/treyfoerster41-creator/IST-402-Project-4/actions/runs/43910474072) passed all of these checks from a clean checkout on November 16, 2026. Codex also verified that the branch could be cloned without signing in.

## Remaining limitations

These candles come from sampled quotes, not a complete exchange trade tape. Missing minutes remain gaps. The execution model does not reproduce liquidity, spread, partial fills, taxes, or market impact. Paper accounts can close candles on a clock tick, while a historical backtest advances its clock at recorded receipts; a sparse feed can therefore change decision timing.

A backtest uses at most the latest 50,000 receipts, with any truncation labeled. Charts show up to 500 points, while saved orders and fills remain available. Stopping a paper account freezes its state without forcing a sale. The AI decision and audio features belong to Part 4.3 and are not included yet.

## Repository and demo

- **GitHub repository:** [IST-402-Project-4](https://github.com/treyfoerster41-creator/IST-402-Project-4)
- **Part 4.2 application commit:** [`3bd8073930d965bc2fde77cb1d6f073e51bc4639`](https://github.com/treyfoerster41-creator/IST-402-Project-4/commit/3bd8073930d965bc2fde77cb1d6f073e51bc4639) on the [Part 4.2 branch](https://github.com/treyfoerster41-creator/IST-402-Project-4/tree/codex/assignment4-part2).
- **Part 4.2 demo video:** [Watch my Signal Desk walkthrough](https://psu.mediaspace.kaltura.com/media/t/1_b8wzer9g) (silent recording, about 1 minute 19 seconds). I recorded the updated interface myself and confirmed that this link works in a private browser on November 16, 2026.

I will upload only this report to Canvas. The source code stays in GitHub, and the demo is hosted on Kaltura.

## Supporting documents

- [README and startup instructions](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/README.md)
- [Strategy, accounting, and SQLite design](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/docs/strategy-design.md)
- [Part 4.2 verification evidence](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/evidence/part-4.2/evidence-log.md)
- [GitHub Actions workflow](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/.github/workflows/checks.yml)
- [Agent instructions](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/AGENTS.md)
- [AI-use disclosure](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/AI-USE.md)
- [Archived Part 4.1 report](https://github.com/treyfoerster41-creator/IST-402-Project-4/blob/codex/assignment4-part2/docs/assignment-4-part-1-report-archive.md)
