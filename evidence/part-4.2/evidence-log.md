# Part 4.2 evidence — November 16, 2026

I used Codex for the technical checks below and reviewed the new code and application myself. My review is separate from the automated results. I preserved my existing Yahoo records and Part 4.1 report. Times are America/New_York unless marked UTC.

## Curated process

| Intent / instruction | Result | Check and observation | Decision / uncertainty |
|---|---|---|---|
| “Display two simple moving averages ... and their crossover.” | `backend/strategy.py`, `frontend/src/indicators.js`, chart series/markers | Batch and rolling-queue SMA values compared with pandas over windows 2, 3, 8, 20, 200; browser display compared with a fixed pandas fixture. | Only completed bars contribute. Equal values keep the last strict side; initial pair is warmup. |
| “using only information available at each decision time” | Receipt-driven `Engine.quote` / `advance` | Prefix and restored-engine tests verify earlier decisions/fills remain the same after later receipts. Late revision test keeps the original frozen close. | Use observation journal receipts, not today's final corrected candles. Upper market and lower decision charts may differ. |
| “Check simulated accounting against known examples.” | Decimal ledger, persisted orders and fills | Two-unit $100/$110 example with 10 bps and $1 fees yields $17.58 realized P/L, $1,017.58 final cash. | Fees enter cost basis; full-position exits only. A review also identified an exit-fee edge case: an exit that would make cash negative is now rejected and tested. |
| “Keep browser tests ... GitHub Actions.” | `frontend/e2e/workstation.spec.js`, isolated server, workflow | Initial run: four passed, one refresh check failed because `innerText` and default `textContent` concatenate layout differently. Recorded amounts matched. Using `useInnerText:true` fixed the assertion; all five passed. | This was a test representation error, not lost persistence. Browser tests use a temporary database and disabled provider. |
| Dependency approval request | Exact-pinned Playwright dev dependency and Chromium | Student replied “hell yeah bro, do whatever you need to.” Installation/build/browser tests succeeded. | No additional backend package was needed; pandas was already present through yfinance. |
| Preserve the existing application | Part 4.1 archive, additive schema, new branch | Original tests still pass; real Yahoo live browser status and source ages observed November 16. | No market database reset or synthetic seeding. |

## Expected versus observed

| Check | Expected | Observed |
|---|---|---|
| Backend suite | SMA reference parity, causal inputs, accurate money, persistence | 27 passed; see [log](backend-tests.txt). |
| Frontend unit suite | SMA/crossover reference parity and receipt replay remain correct | 8 passed; see [log](frontend-tests.txt). |
| Production build | Vue/chart components compile | Passed; see [log](frontend-build.txt). |
| Browser suite | Backtest, saved results, errors, paper controls, responsive layout | 5 passed; see [log](browser-tests.txt). |
| Real Yahoo historical backtest | Receipt-time decisions produce a durable ledger and result | AAPL run `1810370a…`, 15,405 inputs, cutoff receipt #37832, 728 frozen closes, 94 fills, $94 fees, −$104.49 P/L, final equity $9,895.51; [summary](run-proof.json), [screenshot](yahoo-backtest.png). This is actual recorded history, not synthetic practice. |
| Paper account with real source | Warm history without backdated trades, process new receipts | Created AAPL account through the browser at 10:27:39. Reopening retained $10,000 cash, zero position and zero fills; frozen-candle count advanced to 733 and the mark updated. [Screenshot](paper-account.png). No live crossover fill was claimed at this checkpoint. |
| Persistence | Same account/run on refresh; no duplicate fill on repeated processing | Browser refresh/reopening retained saved state; backend test reopens SQLite and repeats the worker pass with identical ledger/state. |
| Unavailable feed / empty history | Useful failure message and offline practice remains usable | Browser harness verified deliberate outage, empty replay, empty real-history error and successful practice backtest. These are controlled tests, not proof of every provider outage. |
| Remote CI | Workflow runs on push and reports all checks | Passed on push for application commit `5cb41d9452b448a7f32953a6895d838bdc555afa`. The [Actions run](https://github.com/treyfoerster41-creator/IST-402-Project-4/actions/runs/43899746943) completed successfully after installing locked dependencies and running backend, frontend/build, and browser checks. See [verification record](ci-verification.json). |

## Submission status

On November 16, 2026, I confirmed that I reviewed the Part 4.2 code in VS Code and the application in the browser, accepted both, and authorized committing, pushing, and verification. The initial reviewed application was committed as `5cb41d9452b448a7f32953a6895d838bdc555afa` and pushed to `codex/assignment4-part2`. The remote Actions run passed, and Codex verified an unauthenticated clone of that branch with a clean working tree. I am using the same repository as Part 4.1. I supplied my [Part 4.2 demo link](https://psu.mediaspace.kaltura.com/media/t/1_b8wzer9g) and confirmed private-browser access on November 16, 2026. I still need to upload the final report to Canvas. I am keeping the Part 4.1 video and report as earlier evidence.

## What the evidence establishes

The deterministic tests establish calculations under the documented execution assumptions. Browser tests establish the user workflows against the real backend with an isolated synthetic/empty dataset. The separate browser backtest establishes integration with the existing Yahoo journal. None proves future profitability, complete exchange history, realistic liquidity, or live AI behavior. See [design](../../docs/strategy-design.md) for receipt/clock, revision, fee and sampling assumptions.

## Final interface and my recorded demo

I asked for a cleaner chart after the repeated BUY/SELL labels obscured the candles. Codex replaced those words with small crossover arrows and a legend, made the SMA lines thinner, added recent-candle and full-view controls, and explained the simulation settings in the interface. All 27 backend tests, 8 frontend tests, 5 browser tests and the production build passed after those changes. Codex also checked the updated page in the browser; I then used that interface in my own recording.

My [silent Kaltura demo](https://psu.mediaspace.kaltura.com/media/t/1_b8wzer9g) shows candlesticks, both SMAs, crossovers, a change to five units, a saved-Yahoo backtest, account results, equity, filled orders and execution assumptions. The mouse pointer is visible. The local recording is 79.465 seconds at 2940 × 1558, with no audio track; I chose to keep this original version. I confirmed that the hosted link works in a private browser. Codex inspected metadata and sampled frames; that review is separate from my access check. See [video verification](video-verification.json), [candle frame](demo-candles.png) and [result frame](demo-results.png).

The recorded run is `920061ad-2a63-4a9b-bfb7-132cc0bafbe1`: 18,664 inputs, cutoff #44914, 786 completed candles, five units per buy, 100 fills, $100 total fees, final equity/cash $9,843.40, realized P/L −$156.60, unrealized P/L $0 and zero final position. Codex read the existing saved run without changing it and matched these numbers to the video; see [demo run proof](demo-run-proof.json). This uses a later receipt cutoff than the original one-unit verification run.

Final application publication: the chart and control refinements shown in my recording are committed as `3bd8073930d965bc2fde77cb1d6f073e51bc4639` on `codex/assignment4-part2`. The [push-triggered Actions run](https://github.com/treyfoerster41-creator/IST-402-Project-4/actions/runs/43910474072) passed from a clean checkout, including all 40 tests and the production build. Its exact commit and step results are saved in [final CI verification](final-application-ci.json). The report identifies this application commit; subsequent report/evidence commits do not change the application code.
