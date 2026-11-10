// Reconstruct only receipts already reached. Source order determines OHLC;
// receipt order determines which revision was known at that point in the replay.
export function buildReplayBars(rows, index) {
  const prefix = rows.slice(0, index);
  const replayClock = prefix.at(-1)?.received_ms ?? 0;
  const slots = new Map();
  for (const row of prefix) slots.set(row.identity, row);
  const ordered = [...slots.values()].sort((a, b) => a.source_ms - b.source_ms || a.seq - b.seq);
  const bars = new Map();
  let previousVolume = null;
  let previousDay = null;
  for (const row of ordered) {
    const time = Math.floor(row.source_ms / 60000) * 60;
    const day = Math.floor(row.source_ms / 86400000);
    if (!bars.has(time)) {
      bars.set(time, { time, open: row.price, high: row.price, low: row.price, close: row.price,
        volume: 0, volume_known: false, complete: (time + 60) * 1000 <= replayClock });
    }
    const bar = bars.get(time);
    bar.high = Math.max(bar.high, row.price);
    bar.low = Math.min(bar.low, row.price);
    bar.close = row.price;
    const currentVolume = row.symbol === 'BTC-USD' ? null : row.day_volume;
    if (currentVolume != null && previousVolume != null && day === previousDay && currentVolume >= previousVolume) {
      bar.volume += currentVolume - previousVolume;
      bar.volume_known = true;
    }
    previousVolume = currentVolume;
    previousDay = day;
  }
  return [...bars.values()];
}
