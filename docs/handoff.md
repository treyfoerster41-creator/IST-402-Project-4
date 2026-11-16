# Part 4.2 handoff

Work on `codex/assignment4-part2` in the separate Assignment 4 folder. The Part 4.1 report is preserved at docs/assignment-4-part-1-report-archive.md. Preserve the ignored market database and its real observations.

Implemented: SMA(3)/SMA(8) overlays and crossover markers; configurable lengths; frozen receipt-time strategy; paper accounts; orders/fills and Decimal accounting; saved-Yahoo and synthetic-practice backtests; equity/drawdown and trade tables; persistent state; backend/reference/frontend/browser tests; Actions workflow on push/PR. No Part 4.3 AI/audio or real trading.

Running locally: frontend http://127.0.0.1:5174/, backend port 8004. Start commands and offline browser harness are in README.

Verification: 27 backend tests, 8 frontend unit tests, 5 browser tests and production build. Real AAPL backtest created through browser: 15,405 receipts, 728 completed strategy candles, 94 fills, −$104.49 P/L after fees/slippage. A separate paper account was started flat and processes new crossover signals. My later five-unit video backtest used 18,664 receipts and 786 closed candles, produced 100 fills, and ended at $9,843.40 (−$156.60 P/L). The original journal was untouched except normal live collection and additive simulation tables.

Publication and submission:
1. DONE: I personally reviewed the new code in VS Code and accepted the Part 4.2 browser behavior on November 16, 2026. I authorized committing, pushing and verification.
2. DONE: The reviewed application is published at `3bd8073930d965bc2fde77cb1d6f073e51bc4639` on `codex/assignment4-part2`. [GitHub Actions](https://github.com/treyfoerster41-creator/IST-402-Project-4/actions/runs/43910474072) passed from a clean checkout, and an earlier unauthenticated clone confirmed public repository access. The application commit and CI result are in report.md and evidence/part-4.2/final-application-ci.json.
3. DONE: I recorded the updated interface with five units per buy, supplied [the Part 4.2 Kaltura video](https://psu.mediaspace.kaltura.com/media/t/1_b8wzer9g), and confirmed private-browser access. The original 79.465-second silent video is my selected version. Its saved run and video review are documented in evidence/part-4.2/.
4. I will upload only report.md to Canvas. Canvas submission is still pending.
