import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backend import main
from backend.store import initialize, ingest, candles, records, persist_candles, connect

class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_failure_and_pause(self):
        main.paused=False
        with patch.object(main.yf,'AsyncWebSocket',side_effect=OSError('private upstream detail')):
            task=asyncio.create_task(main.feed())
            await asyncio.sleep(.03)
            self.assertEqual(main.state['status'],'unavailable')
            self.assertNotIn('private',main.state['detail'])
            task.cancel()
            with self.assertRaises(asyncio.CancelledError): await task
        self.assertTrue(main.control('pause')['paused'])
        self.assertFalse(main.control('resume')['paused'])
    async def test_invalid_symbol(self):
        with self.assertRaises(main.HTTPException): main.observations('INVALID')
    async def test_persisted_completion_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.db';initialize(path)
            ingest({'id':'AAPL','time':60000,'price':10},path,received_ms=90000)
            rows=records('AAPL',path)
            persist_candles('AAPL',candles(rows,90000),90000,path)
            persist_candles('AAPL',candles(rows,90000),90000,path)
            with connect(path) as con:
                r=con.execute('SELECT * FROM candles').fetchone()
                self.assertEqual((r['complete'],r['revision']),(0,1))
            persist_candles('AAPL',candles(rows,120000),120000,path)
            initialize(path)
            with connect(path) as con:
                r=con.execute('SELECT * FROM candles').fetchone()
                self.assertEqual((r['complete'],r['revision']),(1,2))


class StreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_clean_upstream_close_is_detected(self):
        from types import SimpleNamespace
        async def ended():
            if False:
                yield None
        client=SimpleNamespace(_ws=ended())
        async def handle(message):
            self.fail('No message should arrive')
        with self.assertRaises(ConnectionError):
            await main.listen_quotes(client,handle)

    async def test_selected_symbol_staleness(self):
        with patch.object(main,'records',return_value=[]), patch.object(main,'stored_candles',return_value=[]):
            main.paused=False
            main.state.update(status='live',last_received_ms=9999999999999)
            result=main.snapshot('AAPL')
            self.assertEqual(result['feed']['status'],'stale')
            self.assertEqual(result['bars'],[])
