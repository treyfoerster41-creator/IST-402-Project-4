<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { createChart, CandlestickSeries, LineSeries, ColorType, createSeriesMarkers } from 'lightweight-charts';
const props = defineProps({ symbol: String });
const fast = defineModel('fast', { default: 3 });
const slow = defineModel('slow', { default: 8 });
const source = ref('yahoo');
const cash = ref(10000), quantity = ref(1), fee = ref(1), slippage = ref(5);
const runs = ref([]), run = ref(null), selected = ref('');
const busy = ref(false), error = ref('');
const plot = ref(null), equityPlot = ref(null);
const valid = computed(() => Number.isInteger(fast.value) && Number.isInteger(slow.value) && fast.value >= 2 && fast.value < slow.value && slow.value <= 200 && cash.value >= 1 && quantity.value > 0 && fee.value >= 0 && slippage.value >= 0 && slippage.value <= 100);
let chart, candles, fastLine, slowLine, markers, equityChart, equityLine, poll, version = 0, disposed = false;
let fittedRun = null;
const usd = value => Number(value ?? 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
const date = value => value ? new Date(value).toLocaleString() : '—';
const recentSignals = computed(() => run.value?.signals.slice(-6).reverse() ?? []);
async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Check the strategy settings and try again.');
  return data;
}
async function refreshList() {
  const data = await api('/api/trading/runs');
  if (!disposed) runs.value = data.runs;
}
async function showRun(id, quiet = false) {
  const request = ++version;
  try {
    const data = await api(`/api/trading/runs/${id}`);
    if (request !== version || disposed) return;
    run.value = data;
    selected.value = id;
    if (!quiet) error.value = '';
    await nextTick();
    draw();
  } catch (e) {
    if (request === version) error.value = quiet ? 'Account refresh failed; showing the last saved snapshot.' : e.message;
  }
}
async function create(mode) {
  if (!valid.value || busy.value) return;
  ++version;
  busy.value = true; error.value = '';
  try {
    const data = await api('/api/trading/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
      mode, source: source.value, symbol: source.value === 'practice' ? 'AAPL' : props.symbol,
      fast: fast.value, slow: slow.value, cash: cash.value, quantity: quantity.value, fee: fee.value, slippage_bps: slippage.value,
    }) });
    if (disposed) return;
    run.value = data; selected.value = data.id;
    await refreshList(); await nextTick(); draw();
  } catch (e) { error.value = e.message; }
  finally { busy.value = false; }
}
async function stop() {
  if (!run.value || busy.value) return;
  ++version; busy.value = true;
  try {
    run.value = await api(`/api/trading/runs/${run.value.id}/stop`, { method: 'POST' });
    await refreshList(); draw();
  } catch (e) { error.value = e.message; }
  finally { busy.value = false; }
}
function draw() {
  if (!chart || !run.value) return;
  const r = run.value;
  candles.setData(r.points.map(p => ({ time: p.time, open: p.open, high: p.high, low: p.low, close: p.close })));
  fastLine.setData(r.points.filter(p => p.fast != null).map(p => ({ time: p.time, value: p.fast })));
  slowLine.setData(r.points.filter(p => p.slow != null).map(p => ({ time: p.time, value: p.slow })));
  markers.setMarkers(r.points.filter(p => p.crossover).map(p => ({ time: p.time, position: p.crossover === 'buy' ? 'belowBar' : 'aboveBar', color: p.crossover === 'buy' ? '#63dfbb' : '#f77785', shape: p.crossover === 'buy' ? 'arrowUp' : 'arrowDown', text: p.crossover.toUpperCase() })));
  equityLine.setData(r.equity);
  if (fittedRun !== r.id) {
    chart.timeScale().fitContent(); equityChart.timeScale().fitContent(); fittedRun = r.id;
  }
}
watch(() => props.symbol, symbol => { quantity.value = symbol === 'BTC-USD' ? 0.01 : 1; });
onMounted(async () => {
  const options = { autoSize: true, layout: { background: { type: ColorType.Solid, color: '#111b2b' }, textColor: '#a8b7cc' }, grid: { vertLines: { color: '#1d2b40' }, horzLines: { color: '#1d2b40' } }, timeScale: { timeVisible: true } };
  chart = createChart(plot.value, options);
  candles = chart.addSeries(CandlestickSeries, { upColor: '#20c997', downColor: '#f77785', borderVisible: false, wickUpColor: '#20c997', wickDownColor: '#f77785' });
  fastLine = chart.addSeries(LineSeries, { color: '#f0c674', lineWidth: 2, priceLineVisible: false });
  slowLine = chart.addSeries(LineSeries, { color: '#8cb4ff', lineWidth: 2, priceLineVisible: false });
  markers = createSeriesMarkers(candles, []);
  equityChart = createChart(equityPlot.value, options);
  equityLine = equityChart.addSeries(LineSeries, { color: '#63dfbb', lineWidth: 2, priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });
  try {
    await refreshList();
    if (runs.value.length) await showRun(runs.value[0].id);
  } catch { error.value = 'Could not load saved simulations. Check the backend.'; }
  poll = setInterval(() => { if (!busy.value && run.value?.status === 'running') showRun(run.value.id, true); }, 2000);
});
onBeforeUnmount(() => { disposed = true; ++version; clearInterval(poll); chart?.remove(); equityChart?.remove(); });
</script>

<template>
<section class="strategy-desk" aria-labelledby="strategy-title">
  <div class="section-heading"><div><p class="eyebrow">ASSIGNMENT 4.2 / STRATEGY & RESULTS</p><h2 id="strategy-title">Put the crossover to the test.</h2><p>Buy an upward crossover. Sell a downward crossover. Follow the money, one simulated fill at a time.</p></div><span class="simulation-badge">SIMULATED ONLY</span></div>
  <form class="strategy-settings" @submit.prevent="create('backtest')">
    <div class="setting-grid">
      <label>Fast SMA<input aria-label="Fast SMA" type="number" min="2" max="199" step="1" v-model.number="fast"></label>
      <label>Slow SMA<input aria-label="Slow SMA" type="number" min="3" max="200" step="1" v-model.number="slow"></label>
      <label>Starting cash ($)<input type="number" min="1" max="100000000" step=".01" v-model.number="cash"></label>
      <label>Units per buy<input type="number" min=".000001" max="10000" step=".000001" v-model.number="quantity"></label>
      <label>Fee per fill ($)<input type="number" min="0" max="1000" step=".01" v-model.number="fee"></label>
      <label>Slippage (basis points)<input type="number" min="0" max="100" step=".1" v-model.number="slippage"></label>
    </div>
    <div class="run-controls"><label>Backtest data<select v-model="source"><option value="yahoo">Saved Yahoo history · {{symbol}}</option><option value="practice">Synthetic accounting practice</option></select></label><button class="primary" type="submit" :disabled="!valid || busy">{{busy?'Working…':'Run backtest'}}</button><button type="button" @click="create('paper')" :disabled="!valid || busy || source!=='yahoo'">Start paper account</button></div>
    <p v-if="!valid" class="inline-error">Use whole SMA lengths with 2 ≤ fast &lt; slow ≤ 200 and valid positive account settings.</p>
    <p class="assumptions">Completed candles only · Fixed units · Long or flat · Next eligible quote fills · Fees on both sides · 1 basis point = 0.01%. Paper accounts warm up from saved history and trade only after creation.</p>
  </form>
  <p v-if="error" role="alert" class="warning">{{error}}</p>
  <div class="saved-runs"><label>Saved runs<select aria-label="Saved runs" :value="selected" @change="showRun($event.target.value)" :disabled="busy || !runs.length"><option value="" disabled>Choose a saved simulation</option><option v-for="r in runs" :key="r.id" :value="r.id">{{r.mode==='paper'?'Paper account':'Backtest'}} · {{r.source==='practice'?'Practice':r.symbol}} · {{date(r.created_ms)}}</option></select></label><button v-if="run?.status==='running'" :disabled="busy" @click="stop">Stop paper account</button></div>
  <template v-if="run">
    <div class="run-context" data-testid="run-context"><b>{{run.mode==='paper'?'Paper account':'Historical backtest'}} · {{run.symbol}} · {{run.status}}</b><span>{{run.source==='practice'?'SYNTHETIC PRACTICE · invented prices': 'YAHOO RECORDINGS · real saved observations'}}</span><p>{{run.closed_count}} closed candles · SMA {{run.config.fast}} / {{run.config.slow}} · Initial cash {{usd(run.config.cash)}} · {{run.config.quantity}} units · {{usd(run.config.fee)}} per fill · {{run.config.slippage_bps}} bps slippage</p><p>{{run.mode==='paper'?'Collecting new receipts after account creation. Open positions and pending orders remain visible during a feed outage.':'Receipt window: '+date(run.metadata.first_received_ms)+' → '+date(run.metadata.last_received_ms)}} · Input receipts: {{run.metadata.input_count}} · Cutoff #{{run.metadata.cutoff_seq??'—'}}</p></div>
    <div class="account-metrics" data-testid="account-metrics">
      <div><small>ACCOUNT EQUITY</small><strong>{{usd(run.totals.equity)}}</strong><span>{{run.totals.return_pct.toFixed(2)}}% total return</span></div>
      <div><small>CASH</small><strong>{{usd(run.totals.cash)}}</strong><span>{{usd(run.totals.fees)}} total fees</span></div>
      <div><small>POSITION</small><strong>{{Number(run.totals.position)}} units</strong><span>Value {{usd(run.totals.position_value)}}</span></div>
      <div><small>REALIZED P/L</small><strong>{{usd(run.totals.realized)}}</strong><span>Closed trades, after fees</span></div>
      <div><small>UNREALIZED P/L</small><strong>{{usd(run.totals.unrealized)}}</strong><span>Open position, entry fee included</span></div>
      <div><small>MAX DRAWDOWN</small><strong>{{run.totals.max_drawdown_pct.toFixed(2)}}%</strong><span>From observed equity peak</span></div>
    </div>
    <p class="run-note">{{run.pending?'Order pending: waiting for a later eligible quote.':run.fills.length+' fills · '+run.orders.length+' orders'}} · Last mark {{run.totals.mark==null?'unavailable':usd(run.totals.mark)}} at {{date(run.totals.mark_source_ms)}}. {{run.status==='stopped'?'Stopped snapshot; no further fills or mark updates.':''}}</p>
    <p v-if="run.closed_count<run.config.slow" class="warning">Warming up: {{run.closed_count}} / {{run.config.slow}} completed candles. No crossover trades until both averages are ready and change sides.</p>
    <p v-if="run.metadata.truncated" class="warning">This run uses the latest 50,000 receipts. Earlier history was not included.</p>
  </template>
  <div class="results-charts" :class="{'no-result':!run}">
    <div class="chart-card"><div class="chart-title"><b>Decision-time candles & crossovers</b><span class="line-legend"><i class="fast-key"></i>FAST <i class="slow-key"></i>SLOW</span></div><div ref="plot" class="strategy-chart" role="img" aria-label="Frozen decision-time candles with two simple moving averages and crossover markers"></div><p v-if="!run" class="empty">Run a backtest or start a paper account.</p></div>
    <div class="chart-card"><div class="chart-title"><b>Account equity</b><span>CASH + POSITION</span></div><div ref="equityPlot" class="strategy-chart" role="img" aria-label="Simulated account equity over time"></div></div>
  </div>
  <template v-if="run">
    <div class="trade-heading"><h3>Orders & fills</h3><span>Saved in SQLite · USD · {{run.id.slice(0,8)}}</span></div>
    <div class="table-scroll"><table aria-label="Orders and fills"><thead><tr><th>Signal / decision</th><th>Side</th><th>Units</th><th>Status</th><th>Fill price</th><th>Fee</th><th>Realized P/L</th><th>Cash after</th><th>Execution detail</th></tr></thead><tbody><tr v-for="o in run.orders" :key="o.id"><td>{{date(o.decision_ms)}}</td><td :class="o.side==='buy'?'positive':'negative'">{{o.side.toUpperCase()}}</td><td>{{Number(o.quantity)}}</td><td>{{o.status}}</td><td>{{o.fill_id?usd(run.fills[o.fill_id-1].price):'—'}}</td><td>{{o.fill_id?usd(run.fills[o.fill_id-1].fee):'—'}}</td><td>{{o.fill_id?usd(run.fills[o.fill_id-1].realized):'—'}}</td><td>{{o.fill_id?usd(run.fills[o.fill_id-1].cash_after):'—'}}</td><td>{{o.fill_id?'Receipt #'+run.fills[o.fill_id-1].receipt_seq+' · '+date(run.fills[o.fill_id-1].received_ms):o.reason}}</td></tr><tr v-if="!run.orders.length"><td colspan="9">No orders yet. Warmup, no crossover, or an already-flat account can all lead to no trade.</td></tr></tbody></table></div>
    <details class="decision-details"><summary>Recent signals and execution assumptions</summary><ul><li v-for="s in recentSignals" :key="s.time">{{date(s.available_ms)}} · {{s.action.toUpperCase()}} · Fast {{s.fast.toFixed(4)}} / Slow {{s.slow.toFixed(4)}} · {{s.reason}}</li></ul><p>Decisions use closed bars as first known at receipt time. Late revisions stay in market history but cannot rewrite these decisions ({{run.ignored_late}} late receipts skipped by this strategy). Equal averages keep the last strict side; the first complete pair is warmup. Missing minutes are not filled in.</p><p>Fills use the next received quote from a later source minute, with adverse slippage and a fee. A buy is rejected if cash cannot cover it. No shorting or leverage; sell closes the entire position. There is no forced final sale, and an order without a later fill quote is cancelled at backtest end. Open P/L excludes a hypothetical future exit fee.</p><p>Charts show up to 500 decision candles and equity points. Drawdown is calculated over the full processed stream. These sampled, short histories do not establish future profitability or realistic liquidity, spread, market impact, or latency.</p></details>
  </template>
</section>
</template>
