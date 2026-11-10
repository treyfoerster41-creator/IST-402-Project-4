<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { buildReplayBars } from './replay.js';
import { createChart, CandlestickSeries, HistogramSeries, ColorType } from 'lightweight-charts';

const symbol = ref('AAPL');
const mode = ref('live');
const data = ref(null);
const error = ref('');
const transport = ref('connecting');
const now = ref(Date.now());
const rows = ref([]);
const index = ref(0);
const playing = ref(false);
const busy = ref(false);
const container = ref(null);
const visibleBars = ref([]);
let chart, price, volume, socket, timer, replayTimer, reconnectTimer;
let requestVersion = 0;
let disposed = false;
let fitted = false;

const latest = computed(() => mode.value === 'live' ? data.value?.latest : rows.value[index.value - 1]);
const lastBar = computed(() => visibleBars.value.at(-1));
const age = computed(() => latest.value ? Math.max(0, Math.floor((now.value - latest.value.source_ms) / 1000)) + 's' : '—');
const receiptAge = computed(() => latest.value ? Math.max(0, Math.floor((now.value - latest.value.received_ms) / 1000)) + 's' : '—');
const status = computed(() => mode.value === 'replay' ? 'recorded replay'
  : transport.value !== 'connected' ? 'browser ' + transport.value : data.value?.feed.status || 'connecting');

function draw(bars) {
  visibleBars.value = bars;
  if (!price) return;
  price.setData(bars.map(b => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close })));
  volume.setData(bars.filter(b => b.volume_known).map(b => ({
    time: b.time, value: b.volume, color: b.close >= b.open ? '#20c99788' : '#f7778588',
  })));
  if (!fitted && bars.length > 1) {
    chart.timeScale().fitContent();
    fitted = true;
  }
}

function replayBars() {
  draw(buildReplayBars(rows.value, index.value));
}

function connect() {
  if (disposed) return;
  clearTimeout(reconnectTimer);
  // Invalidating the old handle prevents its close/error callbacks affecting the new socket.
  const previous = socket;
  socket = null;
  previous?.close();
  transport.value = 'connecting';
  const active = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/ws/${symbol.value}`);
  socket = active;
  active.onopen = () => { if (socket === active) transport.value = 'connected'; };
  active.onmessage = event => {
    if (socket !== active || disposed) return;
    data.value = JSON.parse(event.data);
    if (mode.value === 'live') draw(data.value.bars);
  };
  active.onclose = () => {
    if (socket !== active || disposed) return;
    transport.value = 'disconnected';
    reconnectTimer = setTimeout(connect, 2000);
  };
  active.onerror = () => { if (socket === active) transport.value = 'disconnected'; };
}

async function loadReplay() {
  const version = ++requestVersion;
  const requestedSymbol = symbol.value;
  busy.value = true;
  error.value = '';
  playing.value = false;
  try {
    const response = await fetch(`/api/observations/${requestedSymbol}`);
    if (!response.ok) throw Error('Replay unavailable');
    const result = await response.json();
    if (version !== requestVersion || requestedSymbol !== symbol.value || disposed) return;
    rows.value = result.rows;
    index.value = Math.min(1, rows.value.length);
    mode.value = 'replay';
    fitted = false;
    replayBars();
    chart.timeScale().fitContent();
  } catch {
    if (version === requestVersion) error.value = 'Could not retrieve recorded observations.';
  } finally {
    if (version === requestVersion) busy.value = false;
  }
}

async function control(action) {
  error.value = '';
  try {
    const response = await fetch(`/api/feed/${action}`, { method: 'POST' });
    if (!response.ok) throw Error('Feed control unavailable');
  } catch {
    error.value = 'Feed control failed. Check the backend.';
  }
}

function live() {
  requestVersion++;
  busy.value = false;
  playing.value = false;
  mode.value = 'live';
  draw(data.value?.bars || []);
  chart.timeScale().fitContent();
}

watch(symbol, () => {
  requestVersion++;
  busy.value = false;
  error.value = '';
  mode.value = 'live';
  playing.value = false;
  rows.value = [];
  data.value = null;
  fitted = false;
  draw([]);
  connect();
});
watch(index, () => { if (mode.value === 'replay') replayBars(); });

onMounted(() => {
  chart = createChart(container.value, {
    autoSize: true,
    layout: { background: { type: ColorType.Solid, color: '#111b2b' }, textColor: '#a8b7cc', attributionLogo: true },
    grid: { vertLines: { color: '#1d2b40' }, horzLines: { color: '#1d2b40' } },
    timeScale: { timeVisible: true, secondsVisible: false },
    rightPriceScale: { borderColor: '#344057' },
  });
  price = chart.addSeries(CandlestickSeries, {
    upColor: '#20c997', downColor: '#f77785', borderVisible: false,
    wickUpColor: '#20c997', wickDownColor: '#f77785',
  });
  price.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0.3 } });
  volume = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'volume' });
  volume.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
  connect();
  timer = setInterval(() => now.value = Date.now(), 1000);
  replayTimer = setInterval(() => {
    if (playing.value && index.value < rows.value.length) index.value++;
    else playing.value = false;
  }, 150);
});

onBeforeUnmount(() => {
  disposed = true;
  requestVersion++;
  clearInterval(timer);
  clearInterval(replayTimer);
  clearTimeout(reconnectTimer);
  socket?.close();
  chart?.remove();
});
</script>
<template>
<main><header><div class="brand">◈ SIGNAL DESK <span>MARKET WORKSTATION</span></div><span class="tag">CLASSROOM · OBSERVATION ONLY</span></header>
<section class="intro"><div><p class="eyebrow">ASSIGNMENT 4.1 / LIVE MARKET DATA</p><h1>A clearer view of the market.</h1><p>Follow the feed. Inspect the record. Replay what actually arrived.</p></div><div class="status" :class="status==='live'?'good':''"><i></i>{{status}}</div></section>
<section class="toolbar"><label>Instrument <select v-model="symbol"><option>AAPL</option><option>MSFT</option><option>BTC-USD</option></select></label><div class="buttons"><button @click="live" :class="{selected:mode==='live'}">Live stream</button><button @click="loadReplay" :disabled="busy" :class="{selected:mode==='replay'}">{{busy?'Loading…':'Recorded replay'}}</button></div><span>1 MINUTE · USD</span></section>
<div v-if="error" role="alert" class="warning">{{error}}</div>
<div v-if="mode==='replay'" class="warning">RECORDED REPLAY · {{rows.length?'Receipt-order playback; no future revisions are included.':'No saved observations for this instrument yet.'}} <button @click="playing=!playing" :disabled="!rows.length">{{playing?'Pause':'Play'}}</button><label>Observation {{index}} / {{rows.length}} <input aria-label="Replay observation" type="range" min="0" :max="rows.length" v-model.number="index"></label></div>
<section class="metrics"><div><small>LAST OBSERVED PRICE</small><strong>{{latest?Number(latest.price).toLocaleString('en-US',{style:'currency',currency:'USD'}):'Waiting'}}</strong></div><div><small>SOURCE DATA AGE</small><strong>{{age}}</strong></div><div><small>RECEIPT AGE</small><strong>{{receiptAge}}</strong></div><div><small>STORED REVISIONS · WINDOW</small><strong>{{mode==='live'?data?.observations??0:rows.length}} <em>/ 10,000 max</em></strong></div></section>
<section class="chart-card"><div class="chart-title"><b>{{symbol}} <span>Sampled price candles & observed volume</span></b><span>{{mode==='live'?'LIVE VIEW':'REPLAY VIEW'}}</span></div><div ref="container" class="chart" role="img" :aria-label="`${symbol} sampled one-minute candles and observed volume`"></div>
<div v-if="lastBar" class="bar-summary">Latest minute · O {{lastBar.open.toFixed(2)}} / H {{lastBar.high.toFixed(2)}} / L {{lastBar.low.toFixed(2)}} / C {{lastBar.close.toFixed(2)}} · Observed volume: {{lastBar.volume_known ? lastBar.volume.toLocaleString() : 'unknown'}} · {{lastBar.complete ? 'elapsed / revisable' : 'provisional'}}</div><p v-if="!latest" class="empty">Waiting for recorded or live Yahoo observations. No synthetic prices are displayed.</p></section>
<section class="details"><article><h2>Know what you’re seeing</h2><p><b>Source:</b> Yahoo Finance via yfinance WebSocket → FastAPI → SQLite → browser WebSocket.</p><p>{{data?.feed.detail||'Connecting to the local backend…'}}</p><p>Quote samples are not a complete trade tape. Volume shows nonnegative changes in reported daily cumulative volume; the first sample and missing/reset values are unknown. Gaps remain gaps. BTC-USD volume is unknown because its counter semantics have not been validated.</p><p>Current minute is provisional. An elapsed candle is closed by time but may still receive late observations or revisions. Visible candle: {{lastBar ? (lastBar.complete ? 'elapsed / revisable' : 'provisional') : 'no candle'}}. Source time: {{latest?new Date(latest.source_ms).toISOString():'—'}}.</p><a href="https://www.tradingview.com/lightweight-charts/" target="_blank" rel="noreferrer">Charts by TradingView Lightweight Charts</a></article><article><h2>Feed resilience</h2><p>Pause the upstream connection to demonstrate an unavailable feed. Saved observations remain available for replay. Controls affect this local server.</p><div class="buttons"><button @click="control('pause')">Simulate feed outage</button><button @click="control('resume')">Reconnect Yahoo</button></div><p>Browser connection: {{transport}}. Stale means no observations for this instrument for 30 seconds. Source age can be older than receipt age.</p><p>Identity: {{latest?.identity||'—'}}<br>Revision: {{latest?.revision||'—'}} · Receipt #{{latest?.seq||'—'}}</p></article></section>
<footer>Local research dashboard · No orders, accounts, or investment recommendations.</footer></main>
</template>
