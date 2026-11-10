import tempfile
import unittest
from pathlib import Path
from backend.store import initialize, ingest, records, candles, stored_candles, connect, recover_materialized

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'test.db'
        initialize(self.path)
    def tearDown(self): self.tmp.cleanup()
    def put(self,t,p,v=100):
        return ingest({'id':'AAPL','time':t,'price':p,'day_volume':v},self.path,received_ms=200000)
    def test_duplicate_revision_out_of_order_restart(self):
        self.assertTrue(self.put(120000,12,120))
        self.assertFalse(self.put(120000,12,120))
        self.assertTrue(self.put(120000,13,125))
        self.assertTrue(self.put(60000,10,100))
        initialize(self.path)
        rows=records('AAPL',self.path)
        self.assertEqual([r['revision'] for r in rows],[1,2,1])
        bars=candles(rows,150000)
        self.assertEqual([b['close'] for b in bars],[10,13])
        self.assertEqual(bars[1]['volume'],25)
        self.assertTrue(bars[0]['complete'])
        self.assertFalse(bars[1]['complete'])
        self.assertEqual(candles(rows[:1],150000)[0]['close'],12)
    def test_missing_volume_reset_invalid(self):
        self.put(60000,10,200)
        self.put(120000,11,100)
        self.assertFalse(candles(records('AAPL',self.path),200000)[1]['volume_known'])
        for value in (float('nan'),-1,0):
            with self.assertRaises(ValueError): self.put(180000,value)
    def test_ohlc_order_and_cutoff(self):
        self.put(61000,10,100)
        self.put(63000,9,130)
        self.put(62000,12,120)
        b=candles(records('AAPL',self.path),120000)[0]
        self.assertEqual((b['open'],b['high'],b['low'],b['close']),(10,12,9,9))
        self.assertEqual(len(records('AAPL',self.path,cutoff=1)),1)

    def test_late_sample_repairs_following_minute_volume(self):
        self.put(60000,10,100)
        self.put(180000,12,200)
        self.put(120000,11,150)
        bars=stored_candles('AAPL',240000,self.path)
        self.assertEqual([b['volume'] for b in bars],[0,50,50])
        self.assertEqual([b['complete'] for b in bars],[1,1,1])

    def test_display_window_cannot_corrupt_stored_open(self):
        # More than the UI cap in one minute: the earliest open must survive.
        with connect(self.path) as con:
            con.executemany("INSERT INTO observations(identity,revision,symbol,source_ms,received_ms,price,day_volume,digest,payload) VALUES(?,1,'AAPL',?,?,?,NULL,?,'{}')",
                            [(f'yahoo:AAPL:{60000+i}',60000+i,90000,20 if i==0 else 10,str(i)) for i in range(10001)])
        self.put(71001,11,150)
        self.assertEqual(len(records('AAPL',self.path)),10000)
        self.assertEqual(stored_candles('AAPL',120000,self.path)[0]['open'],20)
        self.assertEqual(stored_candles('AAPL',120000,self.path)[0]['high'],20)

    def test_zero_cutoff_and_crash_recovery(self):
        self.put(60000,10)
        self.assertEqual(records('AAPL',self.path,cutoff=0),[])
        with connect(self.path) as con:
            con.execute('DELETE FROM candles')  # Disposable test database only.
        recover_materialized(self.path)
        self.assertEqual(stored_candles('AAPL',120000,self.path)[0]['close'],10)

    def test_crypto_volume_is_not_assumed_to_be_session_volume(self):
        rows=[dict(identity='x',seq=1,symbol='BTC-USD',source_ms=60000,price=100,day_volume=1000),
              dict(identity='y',seq=2,symbol='BTC-USD',source_ms=61000,price=101,day_volume=1200)]
        self.assertFalse(candles(rows,120000)[0]['volume_known'])

if __name__=='__main__': unittest.main()
