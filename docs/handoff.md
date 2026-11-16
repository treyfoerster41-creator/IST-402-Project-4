# Part 4.2 handoff

Work on `codex/assignment4-part2` in the separate Assignment 4 folder. The Part 4.1 report is preserved at docs/assignment-4-part-1-report-archive.md. Preserve the ignored market database and its real observations.

Implemented: SMA(3)/SMA(8) overlays and crossover markers; configurable lengths; frozen receipt-time strategy; paper accounts; orders/fills and Decimal accounting; saved-Yahoo and synthetic-practice backtests; equity/drawdown and trade tables; persistent state; backend/reference/frontend/browser tests; Actions workflow on push/PR. No Part 4.3 AI/audio or real trading.

Running locally: frontend http://127.0.0.1:5174/, backend port 8004. Start commands and offline browser harness are in README.

Verification: 27 backend tests, 8 frontend unit tests, 5 browser tests and production build. Real AAPL backtest created through browser: 15,405 receipts, 728 completed strategy candles, 94 fills, −$104.49 P/L after fees/slippage. A separate paper account was started and remains running; it starts flat and will only trade new crossover signals. The original journal was untouched except normal live collection and additive simulation tables.

Remaining:
1. DONE: I personally reviewed the new code in VS Code and accepted the Part 4.2 browser behavior on November 16, 2026. I authorized committing, pushing and verification.
2. DONE: The reviewed application is published at `5cb41d9452b448a7f32953a6895d838bdc555afa` on `codex/assignment4-part2`. [GitHub Actions](https://github.com/treyfoerster41-creator/IST-402-Project-4/actions/runs/43899746943) passed from a clean checkout, and an unauthenticated clone succeeded. The application commit and CI result are in report.md and evidence/part-4.2/ci-verification.json.
3. I still need to record one Part 4.2 demo and supply its accessible link. Follow docs/demo-checklist.md. The old Part 4.1 video is archived, not reused.
4. I will upload only report.md to Canvas once the video link is added. Canvas submission is still pending.
