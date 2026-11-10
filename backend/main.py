import asyncio
import contextlib
import time
import os
import json
import certifi
# Use the installed CA bundle; TLS verification stays enabled.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
import yfinance as yf
from yfinance.config import YfConfig

# Let our supervisor recreate failed connections instead of hiding failures.
YfConfig.debug.hide_exceptions = False
from .store import initialize, ingest, records, stored_candles, recover_materialized, SYMBOLS

state = {'status':'connecting','detail':'Waiting for Yahoo Finance','last_received_ms':None}
paused = False

async def listen_quotes(client, handle):
    """Version-pinned yfinance adapter: closed iterators must terminate.

    yfinance 1.8.0's default listener can spin after a clean upstream close.
    Reuse its subscription/decoder but let our supervisor own reconnection.
    """
    async for raw in client._ws:
        message = json.loads(raw)
        await handle(client._decode_message(message.get('message', '')))
    raise ConnectionError('Yahoo stream closed')


async def feed():
    while True:
        if paused:
            state.update(status='unavailable',detail='Feed deliberately paused for outage demonstration')
            await asyncio.sleep(1)
            continue
        try:
            state.update(status='connecting',detail='Opening Yahoo Finance WebSocket')
            async with yf.AsyncWebSocket(verbose=False) as ws:
                await asyncio.wait_for(ws.subscribe(list(SYMBOLS)), 15)
                async def handle(message):
                    if paused:
                        return
                    try:
                        ingest(message)
                        state.update(status='live',detail='Receiving Yahoo Finance observations',last_received_ms=int(time.time()*1000))
                    except (ValueError,TypeError,OverflowError):
                        state.update(detail='Ignored malformed provider observation')
                state.update(status='waiting',detail='Yahoo connected; waiting for an observation')
                listener = asyncio.create_task(listen_quotes(ws, handle))
                try:
                    while not paused and not listener.done():
                        await asyncio.sleep(1)
                    if listener.done():
                        listener.result()
                        raise ConnectionError('Feed ended')
                finally:
                    listener.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await listener
        except asyncio.CancelledError:
            raise
        except Exception:
            state.update(status='unavailable',detail='Yahoo connection unavailable; retrying in 5 seconds')
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app):
    initialize()
    recover_materialized()
    task=asyncio.create_task(feed())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

app=FastAPI(lifespan=lifespan)

def snapshot(symbol):
    rows=records(symbol)
    now=int(time.time()*1000)
    status=dict(state)
    if paused:
        status.update(status='unavailable',detail='Feed deliberately paused for outage demonstration')
    elif status['status']=='live' and (not rows or now-rows[-1]['received_ms']>30000):
        status.update(status='stale',detail='No recent observations for this instrument; market may be closed')
    bars=stored_candles(symbol,now)
    return dict(symbol=symbol,source='Yahoo Finance via yfinance WebSocket',feed=status,server_ms=now,observations=len(rows),latest=rows[-1] if rows else None,bars=bars,window_limit=10000,chart_limit=500)

@app.get('/api/observations/{symbol}')
def observations(symbol:str):
    if symbol not in SYMBOLS: raise HTTPException(400,'Unsupported symbol')
    return {'source':'Yahoo Finance recorded observations','rows':records(symbol),'limit':10000}

@app.post('/api/feed/{action}')
def control(action:str):
    global paused
    if action not in ('pause','resume'): raise HTTPException(400,'Invalid action')
    paused=action=='pause'
    return {'paused':paused}

@app.websocket('/api/ws/{symbol}')
async def stream(ws:WebSocket,symbol:str):
    await ws.accept()
    if symbol not in SYMBOLS:
        await ws.close(code=1008)
        return
    try:
        while True:
            await ws.send_json(snapshot(symbol))
            try:
                await asyncio.wait_for(ws.receive_text(), 1)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        pass
