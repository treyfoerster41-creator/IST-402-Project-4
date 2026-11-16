import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from pydantic import ValidationError
from backend.strategy import RollingSMA, batch_sma, Engine, side
from backend.trading import RunRequest, create_run, initialize_trading, update_accounts, PRACTICE
from backend.store import initialize, ingest, connect


def config(**changes):
    return RunRequest(**changes).model_dump()


def quote(seq, minute, price, received=None, identity=None):
    return dict(seq=seq, source_ms=minute*60000, received_ms=received or minute*60000+1000,
                identity=identity or f'q:{minute}', price=price, symbol='AAPL', day_volume=seq*10)


class IndicatorTests(unittest.TestCase):
    def test_pandas_reference_and_incremental_batch(self):
        prices=[100,100,100,99,98,97,96,99,103,105,102,97,95,100,106]*50
        for window in (2,3,8,20,200):
            expected=pd.Series(prices).rolling(window, min_periods=window).mean()
            batch=batch_sma(prices,window)
            rolling=RollingSMA(window)
            for i, close in enumerate(prices):
                actual=rolling.update(close)
                if pd.isna(expected.iloc[i]):
                    self.assertIsNone(actual)
                    self.assertIsNone(batch[i])
                else:
                    self.assertAlmostEqual(actual,expected.iloc[i],places=9)
                    self.assertAlmostEqual(actual,batch[i],places=9)

    def test_known_average_and_equal_touch_crossover(self):
        self.assertEqual(batch_sma([2,4,6,8],3),[None,None,4,6])
        self.assertEqual(side(100,100),0)
        self.assertEqual(side(None,100),0)
        # Equality retains the last strict side: touching does not buy/sell twice.
        engine=Engine(config(fast=2,slow=3))
        for i,p in enumerate([3,2,1,1,1,2,3]):
            engine.quote(quote(i+1,i+1,p))
        self.assertEqual([s['action'] for s in engine.s['signals']],['buy'])

    def test_crossover_matches_independent_pandas_reference(self):
        rows=json.loads(PRACTICE.read_text())['rows']
        engine=Engine(config())
        for row in rows:
            engine.quote(row)
        closes=[p['close'] for p in engine.s['points']]
        series=pd.Series(closes)
        fast, slow=series.rolling(3).mean(),series.rolling(8).mean()
        last=0; expected=[]
        for i in range(len(closes)):
            if pd.isna(slow.iloc[i]): continue
            sign=1 if fast.iloc[i]>slow.iloc[i] else -1 if fast.iloc[i]<slow.iloc[i] else 0
            if sign and last and sign!=last:
                expected.append((engine.s['points'][i]['time'],'buy' if sign>0 else 'sell'))
            if sign: last=sign
        self.assertEqual([(s['time'],s['action']) for s in engine.s['signals']], expected)
        self.assertGreater(len(expected),2)

    def test_unfinished_bar_is_excluded_and_revision_frozen(self):
        e=Engine(config(fast=2,slow=3))
        e.quote(quote(1,1,10))
        e.advance(119999)
        self.assertEqual(e.s['closed_count'],0)
        e.advance(120000)
        self.assertEqual(e.s['points'][0]['close'],10)
        e.quote(quote(2,1,999,received=130000,identity='q:1'))
        self.assertEqual(e.s['points'][0]['close'],10)
        self.assertEqual(e.s['ignored_late'],1)

    def test_future_prefix_independence_and_restore(self):
        rows=json.loads(PRACTICE.read_text())['rows']
        whole=Engine(config()); prefix=Engine(config())
        for row in rows[:28]: whole.quote(row)
        checkpoint=copy.deepcopy(whole.s)
        for row in rows[:28]: prefix.quote(row)
        self.assertEqual(prefix.s,checkpoint)
        restored=Engine(config(),json.loads(json.dumps(checkpoint)))
        for row in rows[28:]:
            whole.quote(row); restored.quote(row)
        self.assertEqual(whole.s,restored.s)
        self.assertEqual(whole.s['points'][:len(checkpoint['points'])],checkpoint['points'])
        self.assertEqual(whole.s['fills'][:len(checkpoint['fills'])],checkpoint['fills'])
        self.assertEqual(prefix.s,checkpoint)
        for fill in whole.s['fills']:
            order=whole.s['orders'][fill['order_id']-1]
            self.assertGreater(fill['receipt_seq'],order['decision_seq'])
            self.assertGreaterEqual(fill['source_ms'],(order['signal_time']+60)*1000)


class AccountingTests(unittest.TestCase):
    def test_known_fee_slippage_realized_and_unrealized(self):
        e=Engine(config(cash=1000,quantity=2,fee=1,slippage_bps=10))
        e.signal('buy',dict(time=60,available_ms=120000,as_of_seq=1))
        e.quote(quote(2,2,100))
        self.assertEqual(e.totals()['cash'],'798.80')
        self.assertEqual(e.totals()['cost_basis'],'201.20')
        e.quote(quote(3,3,110))
        self.assertEqual(e.totals()['unrealized'],'18.80')
        e.signal('sell',dict(time=120,available_ms=180000,as_of_seq=3))
        e.quote(quote(4,4,110))
        totals=e.totals()
        self.assertEqual(totals['cash'],'1017.58')
        self.assertEqual(totals['realized'],'17.58')
        self.assertEqual(totals['unrealized'],'0.00')
        self.assertEqual(totals['fees'],'2.00')
        self.assertEqual(totals['total_pnl'],'17.58')

    def test_insufficient_cash_rejects_without_fees(self):
        e=Engine(config(cash=100,quantity=1,fee=1,slippage_bps=0))
        e.signal('buy',dict(time=60,available_ms=120000,as_of_seq=1))
        e.quote(quote(2,2,100))
        self.assertEqual(e.s['orders'][0]['status'],'rejected')
        self.assertEqual(e.s['cash'],'100.00')
        self.assertEqual(e.s['fees'],'0.00')
        self.assertEqual(e.s['fills'],[])

    def test_late_quote_does_not_fill_and_end_does_not_invent_trade(self):
        e=Engine(config())
        e.signal('buy',dict(time=120,available_ms=180000,as_of_seq=2))
        e.quote(quote(3,1,10,received=181000))
        self.assertEqual(len(e.s['fills']),0)
        e.finish()
        self.assertEqual(e.s['orders'][0]['status'],'cancelled')
        self.assertEqual(e.s['position'],'0')

    def test_duplicate_cursor_cannot_double_fill(self):
        e=Engine(config())
        e.signal('buy',dict(time=60,available_ms=120000,as_of_seq=1))
        row=quote(2,2,100)
        e.quote(row); before=copy.deepcopy(e.s); e.quote(row)
        self.assertEqual(before,e.s)

    def test_no_initial_entry_no_shorting_and_future_quote_ignored(self):
        e=Engine(config(fast=2,slow=3))
        for i,p in enumerate([1,2,3,4,5]): e.quote(quote(i+1,i+1,p))
        self.assertEqual(e.s['orders'],[])
        e.signal('sell',dict(time=300,available_ms=360000,as_of_seq=5))
        self.assertEqual(e.s['orders'],[])
        e.quote(quote(6,10,999,received=360000))
        self.assertNotEqual(e.s['mark'],999)
        self.assertEqual(e.s['ignored_future'],1)

    def test_exit_fee_cannot_create_negative_cash(self):
        e=Engine(config(cash=201,quantity=1,fee=100,slippage_bps=0))
        e.signal('buy',dict(time=60,available_ms=120000,as_of_seq=1))
        e.quote(quote(2,2,100))
        e.signal('sell',dict(time=120,available_ms=180000,as_of_seq=2))
        e.quote(quote(3,3,1))
        self.assertEqual(e.s['cash'],'1.00')
        self.assertEqual(e.s['position'],'1.0')
        self.assertEqual(e.s['orders'][-1]['status'],'rejected')

    def test_input_validation(self):
        for params in ({'fast':8,'slow':3},{'cash':float('nan')},{'fee':-1},{'quantity':0},
                       {'slippage_bps':1000},{'source':'unknown'},{'symbol':'INVALID'},
                       {'mode':'paper','source':'practice'}):
            with self.assertRaises(ValidationError): RunRequest(**params)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'market.db'
        initialize(self.path); initialize_trading(self.path)
    def tearDown(self): self.tmp.cleanup()

    def test_practice_persists_auditable_run_orders_fills(self):
        result=create_run(RunRequest(source='practice'),self.path)
        self.assertGreater(len(result['fills']),2)
        self.assertIn('Synthetic',result['metadata']['source_label'])
        initialize(self.path); initialize_trading(self.path)
        with connect(self.path) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM simulated_fills').fetchone()[0],len(result['fills']))
            self.assertEqual(con.execute('SELECT COUNT(*) FROM observations').fetchone()[0],0)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM simulation_runs').fetchone()[0],1)

    def test_saved_yahoo_backtest_empty_and_receipt_cutoff(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException): create_run(RunRequest(),self.path)
        for i,p in enumerate([3,2,1,2,3,4,3,2,1]):
            ingest({'id':'AAPL','time':(i+1)*60000,'price':p},self.path,received_ms=(i+1)*60000+1000)
        result=create_run(RunRequest(fast=2,slow=3),self.path)
        self.assertEqual(result['metadata']['cutoff_seq'],9)
        self.assertEqual(result['closed_count'],8)
        self.assertEqual(result['metadata']['input_count'],9)

    def test_paper_cursor_ledger_and_restart_idempotence(self):
        with patch('backend.trading.time.time',return_value=0):
            result=create_run(RunRequest(mode='paper',fast=2,slow=3),self.path)
        for i,p in enumerate([3,2,1,2,3,4,3,2,1]):
            ingest({'id':'AAPL','time':(i+1)*60000,'price':p},self.path,received_ms=(i+1)*60000+1000)
        update_accounts(self.path,now_ms=541000)
        with connect(self.path) as con:
            before=con.execute('SELECT state_json FROM simulation_runs WHERE id=?',(result['id'],)).fetchone()[0]
            fills=con.execute('SELECT COUNT(*) FROM simulated_fills').fetchone()[0]
        initialize_trading(self.path)
        update_accounts(self.path,now_ms=541000)
        with connect(self.path) as con:
            after=con.execute('SELECT state_json FROM simulation_runs WHERE id=?',(result['id'],)).fetchone()[0]
            self.assertEqual(fills,con.execute('SELECT COUNT(*) FROM simulated_fills').fetchone()[0])
        self.assertEqual(json.loads(before),json.loads(after))
        self.assertGreater(fills,0)
