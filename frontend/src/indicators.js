// Closed bars only. Equality keeps the last strict side; initial warmup is not a signal.
export function indicators(bars, fast = 3, slow = 8) {
  if (!Number.isInteger(fast) || !Number.isInteger(slow) || fast < 2 || fast >= slow || slow > 200) return [];
  const closed = bars.filter(bar => bar.complete);
  let prior = 0;
  return closed.map((bar, index) => {
    const mean = length => index + 1 < length ? null
      : closed.slice(index + 1 - length, index + 1).reduce((sum, b) => sum + b.close, 0) / length;
    const f = mean(fast), s = mean(slow);
    const equal = f == null || s == null || Math.abs(f - s) <= Math.max(1e-10, 1e-12 * Math.max(Math.abs(f), Math.abs(s)));
    const sign = equal ? 0 : f > s ? 1 : -1;
    const crossover = sign && prior && sign !== prior ? (sign > 0 ? 'buy' : 'sell') : null;
    if (sign) prior = sign;
    return { time: bar.time, fast: f, slow: s, crossover };
  });
}
