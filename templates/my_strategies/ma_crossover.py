from tradekit.strategies.base import Strategy
from tradekit.strategies.factory import add_strategy
from tradekit.exec_rules.date_rules.factory import make_datetime_rule
from tradekit.exec_rules.event_rules.factory import make_event_rule
from tradekit.exec_rules.volume_rules.factory import make_volume_rule
import pandas as pd
import numpy as np

class MACrossover(Strategy):
    def __init__(self,
            symbols, 
            capital, 
            interval, 
            stop_rule, 
            profit_rule, 
            date_rules, 
            event_rules, 
            vol_rules,
            timeout,
            fast: int, 
            slow: int 
    ):
        super().__init__(
            symbols=symbols,
            capital=capital,
            interval=interval,
            stop_rule=stop_rule,
            profit_rule=profit_rule,
            date_rules=date_rules,
            event_rules=event_rules,
            vol_rules=vol_rules,
            timeout=timeout
        )
        self.fast = fast
        self.slow = slow
        self._window = slow + 1
        self.sign = None
        self.id = 0

        self.dates = [make_datetime_rule(d) for d in (date_rules or [])]
        self.events = [make_event_rule(d) for d in (event_rules or [])]

    # Creates a buy signal if fast MA of closing price crosses over slow one and buy signal if vice versa
    def on_bar(self, ts, bar, history):
        df = self._add_indicators(history.iloc[-self._window:])
        signal = self._create_signals(df).iloc[-1]

        if signal.enter_long:
            self.id += 1
            type = 1
        elif signal.enter_short:
            self.id += 1
            type = -1
        else:
            return pd.DataFrame()

        # Check if current bar is embargoed by datetime or event restrictions
        if all(e.hit(ts) for e in self.events) and all(d.hit(ts) for d in self.dates):
            vol_args = {'entry_vol': bar['Volume'].values, 'trade_type': type}
            vols = [make_volume_rule(vol_args | d) for d in (self.vol_rules or [])]

            # Check if current bar is embargoed by volume restrictions
            if all(v.hit(vol) for v in vols for vol in bar['Volume'].values):
                return self._build_trade(ts, type)

        return pd.DataFrame()
    
    def signals(self, df):
        full_df = self._add_indicators(df)
        sigs = self._create_signals(full_df)

        mask = sigs['enter_long'].values | sigs['enter_short'].values
        entries = full_df[mask].copy()
        entries['type'] = np.where(entries['enter_long'], 1, -1)

        rows = []

        for ts, entry in entries.iterrows():
            # Check if current bar is embargoed by datetime or event restrictions
            if all(e.hit(ts) for e in self.events) and all(d.hit(ts) for d in self.dates):
                vol_args = {'entry_vol': entry['Volume'].values, 'trade_type': entry['type']}
                vols = [make_volume_rule(vol_args | d) for d in (self.vol_rules or [])]

                # Check if current bar is embargoed by volume restrictions
                if all(v.hit(vol) for v in vols for vol in entry['Volume'].values):
                    self.id += 1
                    rows.append(self._build_trade(ts, entry['type']))

        return pd.concat(rows) if rows else pd.DataFrame()
    
    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df['slow_ma'] = df['Close'].rolling(window=self.slow).mean()
        df['fast_ma'] = df['Close'].rolling(window=self.fast).mean()

        return df
    
    def _create_signals(self, df) -> pd.DataFrame:
        diff = df['fast_ma'] - df['slow_ma']

        sign = np.sign(diff)

        df['sign'] = sign
        df['sign_prev'] = sign.shift(1)

        df['enter_long'] = (df['sign'] == 1) & (df['sign_prev'] <= 0)
        df['enter_short'] = (df['sign'] == -1) & (df['sign_prev'] >= 0)

        return df[['enter_long', 'enter_short']]
    
    def _build_trade(self, ts, type):
        row = {
            'symbols': self.symbols,
            'trade_type': type,
            'capital': self.capital,
            'entry_ts': ts,
            'timeout': self.timeout
        } 

        return pd.DataFrame([row], index=[self.id])


add_strategy('my_strategies.ma_crossover', MACrossover)           
