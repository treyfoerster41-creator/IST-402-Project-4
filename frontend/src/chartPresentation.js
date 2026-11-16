// Shared presentation only; indicator values and trading decisions stay unchanged.
export function crossoverMarkers(points) {
  return points.filter(point => point.crossover).map(point => ({
    time: point.time,
    position: point.crossover === 'buy' ? 'belowBar' : 'aboveBar',
    color: point.crossover === 'buy' ? '#63dfbb' : '#f77785',
    shape: point.crossover === 'buy' ? 'arrowUp' : 'arrowDown',
    size: 0.65,
  }));
}

export function showRecentCandles(chart, count) {
  if (!chart || !count) return;
  chart.timeScale().setVisibleLogicalRange({
    from: Math.max(-1, count - 61),
    to: Math.max(20, count + 3),
  });
}
