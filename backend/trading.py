"""Durable paper accounts and auditable historical runs over the quote journal."""
import asyncio
import json
from pathlib import Path
import threading
import time
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .store import DB, SYMBOLS, connect
from .strategy import Engine

LOCK = threading.RLock()
HISTORY_LIMIT = 50000
PRACTICE = Path(__file__).parent / 'tests' / 'fixtures' / 'practice-quotes.json'
router = APIRouter(prefix='/api/trading')


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    mode: str = 'backtest'
    source: str = 'yahoo'
    symbol: str = 'AAPL'
    fast: int = Field(default=3, ge=2, le=199)
    slow: int = Field(default=8, ge=3, le=200)
    cash: float = Field(default=10000, ge=1, le=100000000, multiple_of=0.01)
    quantity: float = Field(default=1, gt=0, le=10000, multiple_of=0.000001)
    fee: float = Field(default=1, ge=0, le=1000, multiple_of=0.01)
    slippage_bps: float = Field(default=5, ge=0, le=100)

    @model_validator(mode='after')
    def check(self):
        if self.fast >= self.slow:
            raise ValueError('Fast SMA must be shorter than slow SMA')
        if self.symbol not in SYMBOLS or self.source not in ('yahoo', 'practice') or self.mode not in ('paper', 'backtest'):
            raise ValueError('Unsupported symbol, source or mode')
        if self.mode == 'paper' and self.source != 'yahoo':
            raise ValueError('Live paper accounts use Yahoo only')
        if self.source == 'practice' and self.symbol != 'AAPL':
            raise ValueError('The synthetic practice fixture uses AAPL as a demonstration label')
        return self


def initialize_trading(path=DB):
    with connect(path) as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS simulation_runs (
            id TEXT PRIMARY KEY, mode TEXT NOT NULL, status TEXT NOT NULL,
            symbol TEXT NOT NULL, source TEXT NOT NULL, created_ms INTEGER NOT NULL,
            config_json TEXT NOT NULL, metadata_json TEXT NOT NULL, state_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS simulated_orders (
            run_id TEXT NOT NULL REFERENCES simulation_runs(id), id INTEGER NOT NULL,
            side TEXT NOT NULL, status TEXT NOT NULL, decision_ms INTEGER NOT NULL,
            decision_seq INTEGER NOT NULL, detail_json TEXT NOT NULL, PRIMARY KEY(run_id,id));
        CREATE TABLE IF NOT EXISTS simulated_fills (
            run_id TEXT NOT NULL REFERENCES simulation_runs(id), id INTEGER NOT NULL,
            order_id INTEGER NOT NULL, receipt_seq INTEGER NOT NULL, price TEXT NOT NULL,
            quantity TEXT NOT NULL, fee TEXT NOT NULL, detail_json TEXT NOT NULL, PRIMARY KEY(run_id,id));
        ''')


def history(symbol, path=DB):
    with connect(path) as con:
        count = con.execute('SELECT COUNT(*) FROM observations WHERE symbol=?', (symbol,)).fetchone()[0]
        rows = con.execute('SELECT * FROM observations WHERE symbol=? ORDER BY seq DESC LIMIT ?',
                           (symbol,HISTORY_LIMIT)).fetchall()
    return [dict(r) for r in reversed(rows)], count


def save_state(con, run_id, engine):
    s = engine.s
    con.execute('UPDATE simulation_runs SET state_json=? WHERE id=?', (json.dumps(s, allow_nan=False),run_id))
    for order in s['orders']:
        con.execute('INSERT INTO simulated_orders VALUES(?,?,?,?,?,?,?) ON CONFLICT(run_id,id) DO UPDATE SET status=excluded.status, detail_json=excluded.detail_json',
                    (run_id,order['id'],order['side'],order['status'],order['decision_ms'],order['decision_seq'],json.dumps(order)))
    for fill in s['fills']:
        con.execute('INSERT OR IGNORE INTO simulated_fills VALUES(?,?,?,?,?,?,?,?)',
                    (run_id,fill['id'],fill['order_id'],fill['receipt_seq'],fill['price'],fill['quantity'],fill['fee'],json.dumps(fill)))


def present(row):
    data = dict(row)
    config, state, meta = [json.loads(data.pop(key)) for key in ('config_json','state_json','metadata_json')]
    engine = Engine(config,state)
    return dict(**data, config=config, metadata=meta, totals=engine.totals(),
                points=state['points'], equity=state['equity'], orders=state['orders'], fills=state['fills'],
                signals=state['signals'], closed_count=state['closed_count'], last_seq=state['last_seq'],
                ignored_late=state['ignored_late'], ignored_future=state['ignored_future'],
                pending=state['pending'] is not None, clock_ms=state['clock_ms'])


def create_run(request, path=DB):
    config = request.model_dump()
    with LOCK:
        if request.source == 'practice':
            fixture = json.loads(PRACTICE.read_text())
            rows, count = fixture['rows'], len(fixture['rows'])
            source = fixture['source']
        else:
            rows, count = history(request.symbol,path)
            source = 'Saved Yahoo Finance WebSocket observations, replayed in receipt order'
        if request.mode == 'backtest' and not rows:
            raise HTTPException(409,'No saved Yahoo observations for this instrument. Collect live data or choose synthetic practice.')
        engine = Engine(config)
        for row in rows:
            engine.quote(row, trade=request.mode == 'backtest')
        now = int(time.time()*1000)
        if request.mode == 'paper':
            engine.advance(now,trade=False)
            # Warmup uses history for indicators only. Account performance starts now.
            engine.s['equity'] = []
            engine.record_equity(now//1000)
        else:
            engine.finish()
        meta = dict(source_label=source, input_count=len(rows), available_count=count,
                    truncated=count>len(rows), first_seq=rows[0]['seq'] if rows else None,
                    cutoff_seq=rows[-1]['seq'] if rows else None,
                    first_received_ms=rows[0]['received_ms'] if rows else None,
                    last_received_ms=rows[-1]['received_ms'] if rows else None,
                    assumptions='Long or flat; fixed quantity; full fills at next eligible received quote; entry cost includes fee; no leverage, shorting, interest, taxes or forced final sale.')
        run_id = str(uuid.uuid4())
        with connect(path) as con:
            con.execute('INSERT INTO simulation_runs VALUES(?,?,?,?,?,?,?,?,?)',
                        (run_id,request.mode,'running' if request.mode=='paper' else 'completed',request.symbol,request.source,now,
                         json.dumps(config),json.dumps(meta),json.dumps(engine.s)))
            save_state(con,run_id,engine)
            return present(con.execute('SELECT * FROM simulation_runs WHERE id=?',(run_id,)).fetchone())


def update_accounts(path=DB, now_ms=None):
    with LOCK, connect(path) as con:
        runs=con.execute("SELECT * FROM simulation_runs WHERE mode='paper' AND status='running'").fetchall()
        for run in runs:
            engine=Engine(json.loads(run['config_json']),json.loads(run['state_json']))
            rows=con.execute('SELECT * FROM observations WHERE symbol=? AND seq>? ORDER BY seq LIMIT 5000',
                             (run['symbol'],engine.s['last_seq'])).fetchall()
            for row in rows:
                engine.quote(dict(row))
            if len(rows)<5000:
                engine.advance(now_ms if now_ms is not None else int(time.time()*1000))
            save_state(con,run['id'],engine)


async def account_worker():
    while True:
        # One local worker; transaction includes cursor, ledger and strategy state.
        await asyncio.to_thread(update_accounts)
        await asyncio.sleep(1)


@router.get('/runs')
def list_runs():
    with connect() as con:
        rows=con.execute('SELECT id,mode,status,symbol,source,created_ms FROM simulation_runs ORDER BY created_ms DESC LIMIT 50').fetchall()
    return {'runs':[dict(r) for r in rows]}


@router.post('/runs')
def new_run(request: RunRequest):
    return create_run(request)


@router.get('/runs/{run_id}')
def get_run(run_id: str):
    with connect() as con:
        row=con.execute('SELECT * FROM simulation_runs WHERE id=?',(run_id,)).fetchone()
    if row is None:
        raise HTTPException(404,'Run not found')
    return present(row)


@router.post('/runs/{run_id}/stop')
def stop_run(run_id: str):
    with LOCK, connect() as con:
        row=con.execute('SELECT * FROM simulation_runs WHERE id=?',(run_id,)).fetchone()
        if row is None:
            raise HTTPException(404,'Run not found')
        if row['mode']!='paper':
            raise HTTPException(409,'Only paper accounts can be stopped')
        engine=Engine(json.loads(row['config_json']),json.loads(row['state_json']))
        if engine.s['pending'] is not None:
            engine.s['orders'][engine.s['pending']].update(status='cancelled',reason='Account stopped before a fill')
            engine.s['pending']=None
        save_state(con,run_id,engine)
        con.execute("UPDATE simulation_runs SET status='stopped' WHERE id=?",(run_id,))
        return present(con.execute('SELECT * FROM simulation_runs WHERE id=?',(run_id,)).fetchone())
