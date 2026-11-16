# Part 4.2 demo — one 45–60 second video

Use the running dashboard with AAPL selected. Have the saved Yahoo backtest selected in **Saved runs** so the result and trade table are ready. A live market is useful for the upper chart but is not required to rerun recorded history.

1. **0–12 seconds:** Show the price chart and the gold/blue SMA lines. Say: “I added two moving averages and crossover signals. Only completed candles count.”
2. **12–25 seconds:** Show the strategy settings, choose Saved Yahoo history, and click Run backtest. Say: “This replays my recorded Yahoo observations in receipt order. Orders fill on a later quote with fees and slippage.”
3. **25–42 seconds:** Show cash, position, realized/unrealized P/L, equity chart and Orders & fills. Say: “The account tracks each fill and its effect on cash and profit. This result is for the recorded sample, not a prediction.”
4. **42–55 seconds:** Refresh and show the saved result remains, then briefly show the passing GitHub Actions run once published. Say: “The results persist in SQLite. I checked the moving averages against pandas and tested the accounting against a known example.”

The chosen test can lose money; profitability is not required. If using Synthetic accounting practice instead, explicitly call it invented test data and do not describe it as Yahoo history. Record a new Part 4.2 video and check its link without signing in. Add that link and the reviewed application commit to report.md. Submit only report.md to Canvas.

## Selected recording — November 16, 2026

I recorded a silent walkthrough with my cursor visible, changed Units per buy to 5, ran the saved-Yahoo backtest, and showed its account results, charts, orders/fills and execution assumptions. I selected the original 79.465-second recording and confirmed [the Kaltura link](https://psu.mediaspace.kaltura.com/media/t/1_b8wzer9g) in a private browser. This is the selected video; the shorter script above is the original recording plan. See [video verification](../evidence/part-4.2/video-verification.json) and [the demo run](../evidence/part-4.2/demo-run-proof.json).
