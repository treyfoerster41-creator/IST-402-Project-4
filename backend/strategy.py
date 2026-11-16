"""Receipt-time SMA decisions and a long-only paper ledger. No broker calls."""
from collections import deque
from decimal import Decimal, ROUND_HALF_UP
import math


def decimal(value):
    return Decimal(str(value))


def money(value):
    return decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class RollingSMA:
    def __init__(self, length):
        if not isinstance(length, int) or length < 1:
            raise ValueError('SMA length must be a positive integer')
        self.length = length
        self.values = deque()
        self.total = 0.0

    def update(self, close):
        if not math.isfinite(close):
            raise ValueError('Close must be finite')
        self.values.append(close)
        self.total += close
        if len(self.values) > self.length:
            self.total -= self.values.popleft()
        return self.total / self.length if len(self.values) == self.length else None


def batch_sma(closes, length):
    return [None if i + 1 < length else math.fsum(closes[i + 1 - length:i + 1]) / length
            for i in range(len(closes))]


def side(fast, slow):
    if fast is None or slow is None or math.isclose(fast, slow, abs_tol=1e-10, rel_tol=1e-12):
        return 0
    return 1 if fast > slow else -1


def initial_state(config):
    return dict(last_seq=0, clock_ms=0, last_closed=-1, open_bars={}, closes=[],
                prior_side=0, cash=str(money(config['cash'])), position='0', cost_basis='0.00',
                realized='0.00', fees='0.00', mark=None, mark_source_ms=-1,
                orders=[], fills=[], signals=[], points=[], equity=[], pending=None,
                closed_count=0, ignored_late=0, ignored_future=0, peak=str(money(config['cash'])),
                max_drawdown=0.0)


class Engine:
    """One state machine used both online and on historical receipt prefixes.

    A receipt first closes bars using PREVIOUSLY received data. Any resulting
    order may fill on this new receipt, never on its signal candle's close.
    Closed strategy inputs are frozen; the market chart can still revise bars.
    """
    def __init__(self, config, state=None):
        self.config = config
        self.s = state if state is not None else initial_state(config)
        self.fast = RollingSMA(config['fast'])
        self.slow = RollingSMA(config['slow'])
        for close in self.s['closes']:
            self.fast.update(close)
            self.slow.update(close)

    def advance(self, now_ms, trade=True):
        s = self.s
        s['clock_ms'] = max(s['clock_ms'], int(now_ms))
        matured = sorted(int(t) for t in s['open_bars'] if (int(t) + 60) * 1000 <= s['clock_ms'])
        for t in matured:
            slots = s['open_bars'].pop(str(t))
            if t <= s['last_closed']:
                continue
            quotes = sorted(slots.values(), key=lambda r: (r['source_ms'], r['seq']))
            prices = [r['price'] for r in quotes]
            close = prices[-1]
            f, l = self.fast.update(close), self.slow.update(close)
            sign = side(f, l)
            direction = None
            if sign and s['prior_side'] and sign != s['prior_side']:
                direction = 'buy' if sign > 0 else 'sell'
            if sign:
                s['prior_side'] = sign
            s['closes'] = (s['closes'] + [close])[-self.config['slow']:]
            s['last_closed'] = t
            s['closed_count'] += 1
            point = dict(time=t, open=prices[0], high=max(prices), low=min(prices), close=close,
                         fast=f, slow=l, crossover=direction, available_ms=s['clock_ms'], as_of_seq=s['last_seq'])
            s['points'] = (s['points'] + [point])[-500:]
            if direction and trade:
                self.signal(direction, point)
            self.record_equity(t)

    def signal(self, direction, point):
        s = self.s
        reason = 'Order queued for a later eligible quote'
        eligible = (direction == 'buy' and decimal(s['position']) == 0) or (direction == 'sell' and decimal(s['position']) > 0)
        if s['pending'] is not None:
            old = s['orders'][s['pending']]
            old.update(status='cancelled', reason='Superseded by a later crossover before a fill')
            s['pending'] = None
        if eligible:
            order = dict(id=len(s['orders']) + 1, side=direction, status='pending',
                         signal_time=point['time'], decision_ms=point['available_ms'],
                         decision_seq=point['as_of_seq'], quantity=self.config['quantity'] if direction == 'buy' else s['position'],
                         reason=reason, fill_id=None)
            s['orders'].append(order)
            s['pending'] = len(s['orders']) - 1
        else:
            reason = 'Already holding a position' if direction == 'buy' else 'No position to sell'
        s['signals'].append(dict(**point, action=direction, reason=reason))

    def fill(self, row):
        s = self.s
        if s['pending'] is None:
            return
        order = s['orders'][s['pending']]
        if row['seq'] <= order['decision_seq'] or row['source_ms'] < (order['signal_time'] + 60) * 1000:
            return
        qty = decimal(order['quantity'])
        adjustment = decimal(self.config['slippage_bps']) / 10000
        price = (decimal(row['price']) * (1 + adjustment if order['side'] == 'buy' else 1 - adjustment)).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)
        gross, fee = money(price * qty), money(self.config['fee'])
        cash = decimal(s['cash'])
        if order['side'] == 'buy' and gross + fee > cash:
            order.update(status='rejected', reason='Insufficient simulated cash including fees')
            s['pending'] = None
            return
        if order['side'] == 'sell' and cash + gross < fee:
            order.update(status='rejected', reason='Insufficient simulated cash to cover the exit fee')
            s['pending'] = None
            return
        realized = Decimal(0)
        if order['side'] == 'buy':
            s.update(cash=str(cash - gross - fee), position=str(qty), cost_basis=str(gross + fee))
        else:
            realized = gross - fee - decimal(s['cost_basis'])
            s.update(cash=str(cash + gross - fee), position='0', cost_basis='0.00',
                     realized=str(decimal(s['realized']) + realized))
        s['fees'] = str(decimal(s['fees']) + fee)
        fill = dict(id=len(s['fills']) + 1, order_id=order['id'], side=order['side'], quantity=str(qty),
                    price=str(price), gross=str(gross), fee=str(fee), realized=str(realized),
                    source_ms=row['source_ms'], received_ms=row['received_ms'], receipt_seq=row['seq'],
                    cash_after=s['cash'], position_after=s['position'])
        s['fills'].append(fill)
        order.update(status='filled', fill_id=fill['id'], reason='Filled at next eligible received quote with configured slippage')
        s['pending'] = None

    def quote(self, row, trade=True):
        s = self.s
        if row['seq'] <= s['last_seq']:
            return  # durable cursor makes refresh/restart idempotent
        self.advance(row['received_ms'], trade=trade)
        if row['source_ms'] > s['clock_ms']:
            s['ignored_future'] += 1
            s['last_seq'] = row['seq']
            return
        if trade:
            self.fill(row)
        # Late historical quotes cannot roll the account mark backwards.
        if row['source_ms'] >= s['mark_source_ms']:
            s['mark'], s['mark_source_ms'] = row['price'], row['source_ms']
        bucket = row['source_ms'] // 60000 * 60
        if bucket <= s['last_closed']:
            s['ignored_late'] += 1
        else:
            slots = s['open_bars'].setdefault(str(bucket), {})
            slots[row['identity']] = {k: row[k] for k in ('price', 'source_ms', 'seq')}
        s['last_seq'] = row['seq']
        self.record_equity(row['source_ms'] // 1000)

    def totals(self):
        s = self.s
        value = money(decimal(s['position']) * decimal(s['mark'] or 0))
        unrealized = value - decimal(s['cost_basis'])
        equity = decimal(s['cash']) + value
        total = equity - decimal(self.config['cash'])
        return dict(cash=s['cash'], position=s['position'], cost_basis=s['cost_basis'],
                    position_value=str(value), realized=s['realized'], unrealized=str(unrealized),
                    equity=str(equity), total_pnl=str(money(total)), fees=s['fees'],
                    return_pct=float(total / decimal(self.config['cash']) * 100),
                    max_drawdown_pct=s['max_drawdown'], mark=s['mark'], mark_source_ms=s['mark_source_ms'])

    def record_equity(self, t):
        values = self.totals()
        equity = decimal(values['equity'])
        peak = max(decimal(self.s['peak']), equity)
        self.s['peak'] = str(peak)
        self.s['max_drawdown'] = max(self.s['max_drawdown'], float((peak-equity)/peak*100))
        point = dict(time=max(int(t), self.s['clock_ms']//1000), value=float(equity))
        if self.s['equity'] and self.s['equity'][-1]['time'] == point['time']:
            self.s['equity'][-1] = point
        else:
            self.s['equity'] = (self.s['equity'] + [point])[-500:]

    def finish(self):
        if self.s['pending'] is not None:
            self.s['orders'][self.s['pending']].update(status='cancelled', reason='End of data: no later eligible fill quote')
            self.s['pending'] = None
        # No artificial final bar, final price, or forced liquidation.
