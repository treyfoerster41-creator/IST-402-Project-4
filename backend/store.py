"""Append-only Yahoo observation revisions; deterministic sampled-price bars."""
from contextlib import contextmanager
import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path

DB = Path(__file__).parent / 'data' / 'market.db'
SYMBOLS = ('AAPL', 'MSFT', 'BTC-USD')

@contextmanager
def connect(path=DB):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        with con:
            yield con
    finally:
        con.close()

def initialize(path=DB):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as con:
        con.executescript('''PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS observations (
          seq INTEGER PRIMARY KEY AUTOINCREMENT,
          identity TEXT NOT NULL, revision INTEGER NOT NULL,
          symbol TEXT NOT NULL, source_ms INTEGER NOT NULL,
          received_ms INTEGER NOT NULL, price REAL NOT NULL,
          day_volume INTEGER, digest TEXT NOT NULL, payload TEXT NOT NULL,
          UNIQUE(identity, revision), UNIQUE(identity, digest));
        CREATE INDEX IF NOT EXISTS by_symbol ON observations(symbol,seq);
        CREATE INDEX IF NOT EXISTS by_source ON observations(symbol,source_ms,seq);
        CREATE TABLE IF NOT EXISTS candles (
          symbol TEXT NOT NULL, time INTEGER NOT NULL, open REAL NOT NULL,
          high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,
          volume INTEGER NOT NULL, volume_known INTEGER NOT NULL,
          complete INTEGER NOT NULL, revision INTEGER NOT NULL,
          updated_ms INTEGER NOT NULL, PRIMARY KEY(symbol,time));
        ''')

def ingest(message, path=DB, received_ms=None):
    symbol = message.get('id')
    price = float(message.get('price', 0))
    source = int(message.get('time', 0))
    volume = message.get('day_volume')
    volume = None if volume is None else int(volume)
    if symbol not in SYMBOLS or not math.isfinite(price) or price <= 0 or source <= 0 or (volume is not None and volume < 0):
        raise ValueError('Invalid provider observation')
    # Yahoo has no exchange trade ID: identity is explicitly a timestamped quote slot.
    identity = f'yahoo:{symbol}:{source}'
    payload = json.dumps(message, sort_keys=True, separators=(',', ':'), allow_nan=False)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    with connect(path) as con:
        if con.execute('SELECT 1 FROM observations WHERE identity=? AND digest=?', (identity,digest)).fetchone():
            return False
        revision = con.execute('SELECT COALESCE(MAX(revision),0)+1 FROM observations WHERE identity=?', (identity,)).fetchone()[0]
        con.execute('INSERT INTO observations(identity,revision,symbol,source_ms,received_ms,price,day_volume,digest,payload) VALUES(?,?,?,?,?,?,?,?,?)', (identity,revision,symbol,source,received_ms or int(time.time()*1000),price,volume,digest,payload))
    now_ms = received_ms or int(time.time()*1000)
    rebuild_affected(symbol, source, now_ms, path)
    return True

def records(symbol, path=DB, cutoff=None):
    with connect(path) as con:
        # A bounded latest receipt window; replay uses only this window and says so.
        rows = con.execute('SELECT * FROM observations WHERE symbol=? AND seq<=? ORDER BY seq DESC LIMIT 10000', (symbol,cutoff if cutoff is not None else 9223372036854775807)).fetchall()
    return [dict(r) for r in reversed(rows)]

def candles(rows, now_ms):
    latest = {r['identity']: r for r in rows}
    ordered = sorted(latest.values(), key=lambda r:(r['source_ms'],r['seq']))
    bars = {}
    previous_volume = None
    previous_day = None
    for row in ordered:
        bucket = row['source_ms']//60000*60
        day = row['source_ms']//86400000
        # Crypto counter semantics are not validated as cumulative session volume.
        current = None if row.get('symbol') == 'BTC-USD' else row['day_volume']
        delta = None
        if current is not None and previous_volume is not None and day == previous_day and current >= previous_volume:
            delta = current-previous_volume
        previous_volume,previous_day = current,day
        if bucket not in bars:
            bars[bucket] = dict(time=bucket,open=row['price'],high=row['price'],low=row['price'],close=row['price'],volume=0,volume_known=False,complete=(bucket+60)*1000 <= now_ms)
        b = bars[bucket]
        b.update(high=max(b['high'],row['price']),low=min(b['low'],row['price']),close=row['price'])
        if delta is not None:
            b['volume'] += delta
            b['volume_known'] = True
    return list(bars.values())


def persist_candles(symbol, bars, now_ms, path=DB):
    """Materialized current bars. The observation journal preserves prior revisions."""
    with connect(path) as con:
        for b in bars:
            fields = (b['open'], b['high'], b['low'], b['close'], b['volume'], int(b['volume_known']), int(b['complete']))
            old = con.execute('SELECT open,high,low,close,volume,volume_known,complete,revision FROM candles WHERE symbol=? AND time=?',(symbol,b['time'])).fetchone()
            if old is not None and tuple(old)[:7] == fields:
                continue
            revision = old['revision']+1 if old else 1
            con.execute('INSERT OR REPLACE INTO candles VALUES(?,?,?,?,?,?,?,?,?,?,?)', (symbol,b['time'],*fields,revision,now_ms))


def rebuild_affected(symbol, source_ms, now_ms, path=DB):
    """Use the whole journal for affected minutes, never a truncated UI window.

    A late quote can also change the next sample's volume delta, so rebuild its
    minute too. Each minute includes its actual predecessor for the baseline.
    """
    starts = {source_ms // 60000 * 60000}
    with connect(path) as con:
        following = con.execute(
            'SELECT source_ms FROM observations WHERE symbol=? AND source_ms>? '
            'ORDER BY source_ms,seq DESC LIMIT 1', (symbol, source_ms)
        ).fetchone()
        if following:
            starts.add(following['source_ms'] // 60000 * 60000)
        rebuilt = []
        for start in starts:
            previous = con.execute(
                'SELECT * FROM observations WHERE symbol=? AND source_ms<? '
                'ORDER BY source_ms DESC,seq DESC LIMIT 1', (symbol,start)
            ).fetchone()
            current = con.execute(
                'SELECT o.* FROM observations o WHERE symbol=? AND source_ms>=? '
                'AND source_ms<? AND NOT EXISTS '
                '(SELECT 1 FROM observations n WHERE n.identity=o.identity AND n.seq>o.seq) '
                'ORDER BY source_ms,seq', (symbol,start,start+60000)
            ).fetchall()
            inputs = ([dict(previous)] if previous else []) + [dict(r) for r in current]
            rebuilt.extend(b for b in candles(inputs,now_ms) if b['time']==start//1000)
    persist_candles(symbol,rebuilt,now_ms,path)


def stored_candles(symbol, now_ms, path=DB):
    with connect(path) as con:
        # Close elapsed bars even without new provider observations.
        con.execute('UPDATE candles SET complete=1,revision=revision+1,updated_ms=? '
                    'WHERE complete=0 AND (time+60)*1000<=?', (now_ms,now_ms))
        rows = con.execute('SELECT * FROM candles WHERE symbol=? ORDER BY time DESC LIMIT 500',
                           (symbol,)).fetchall()
    return [dict(r) for r in reversed(rows)]


def recover_materialized(path=DB):
    """Recover a possible journal/materialization crash gap on startup."""
    now_ms = int(time.time()*1000)
    with connect(path) as con:
        minutes = con.execute('SELECT symbol, MIN(source_ms) source_ms FROM observations '
                              'GROUP BY symbol, source_ms/60000').fetchall()
    for minute in minutes:
        rebuild_affected(minute['symbol'],minute['source_ms'],now_ms,path)
