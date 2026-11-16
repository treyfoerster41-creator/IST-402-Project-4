# Part 4.2 handoff

Work on `codex/assignment4-part2` in the separate Assignment 4 folder. The Part 4.1 report is preserved at docs/assignment-4-part-1-report-archive.md. Preserve the ignored market database and its real observations.

Implemented: SMA(3)/SMA(8) overlays and crossover markers; configurable lengths; frozen receipt-time strategy; paper accounts; orders/fills and Decimal accounting; saved-Yahoo and synthetic-practice backtests; equity/drawdown and trade tables; persistent state; backend/reference/frontend/browser tests; Actions workflow on push/PR. No Part 4.3 AI/audio or real trading.

Running locally: frontend http://127.0.0.1:5174/, backend port 8004. Start commands and offline browser harness are in README.

Verification: 27 backend tests, 8 frontend unit tests, 5 browser tests and production build. Real AAPL backtest created through browser: 15,405 receipts, 728 completed strategy candles, 94 fills, −$104.49 P/L after fees/slippage. A separate paper account was started and remains running; it starts flat and will only trade new crossover signals. The original journal was untouched except normal live collection and additive simulation tables.

Remaining:
1. DONE: I personally reviewed the new code in VS Code and accepted the Part 4.2 browser behavior on November 16, 2026. I authorized committing, pushing and verification.
2. Commit/push the reviewed Part 4.2 branch, verify the GitHub Actions run and record its URL/result. Add the actual application commit to report.md.
3. Student records one Part 4.2 demo and supplies its accessible link. Follow docs/demo-checklist.md. The old Part 4.1 video is archived, not reused.
4. Upload only report.md to Canvas once the commit/video fields are filled. Do not claim submission until the student confirms it.
