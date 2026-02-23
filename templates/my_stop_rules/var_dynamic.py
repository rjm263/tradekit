from tradekit.exec_rules.stop.base import StopRule
from tradekit.exec_rules.stop.factory import add_stop
import numpy.typing as npt
import numpy as np
import pandas as pd
from collections import deque

class VarDynamicStop(StopRule):
    def __init__(self, entry_price, trade_type, bps: npt.NDArray, window: npt.NDArray, pct: npt.NDArray):
        super().__init__(entry_price, trade_type)
        self.bps = np.atleast_1d(bps)
        self.window = np.atleast_1d(window)
        self.pct = np.atleast_1d(pct)
        self._level = entry_price * (1 - self.trade_type * self.bps / 10000)
        self.buffer = deque()

    def to_state(self) -> dict:
        return {'entry_price': self.entry_price,
                'trade_type': self.trade_type,
                'bps': self.bps,
                'window': self.window,
                'pct': self.pct,
                'level': self.level,
                'buffer': self.buffer}
    
    def hit(self, bar):
        cond = np.where(self.trade_type == 1,
                      self.level >= bar['Low'].values,
                      self.level <= bar['High'].values)
        
        return cond.all()

    def update(self, bar: pd.Series):
        self.buffer.append(bar['Close'].values)
        if len(self.buffer) >= self.window:
            if self.trade_type == 1:
                new_price = np.maximum(self.buffer)
            else:
                new_price = np.minimum(self.buffer)
            ref_price = deque[0]
            self._level = (new_price * (1 - self.trade_type * self.bps / 10000) 
                           + self.pct * (new_price - ref_price))
            self.buffer.clear()

    def exit_mask(self, df) -> npt.NDArray:
        n = self.window
        type = self.trade_type
        bps = self.bps
        pct = self.pct
        entry_price = self.entry_price

        masks = []

        for i in range(len(type)):
            if type[i] == 1:
                price = df['Low'].to_numpy()
                blocks = np.lib.stride_tricks.sliding_window_view(price[:, i], n)[::n-1]
                
                extremes = [entry_price[i]] + [b.max() for b in blocks]
            else:
                price = df['High'].to_numpy()
                blocks = np.lib.stride_tricks.sliding_window_view(price[:, i], n)[::n-1]
            
                extremes = [entry_price[i]] + [b.min() for b in blocks]
            
            rolling_extreme = np.repeat(extremes, n-1)[:len(price[:, i])]
            
            refs = [entry_price[i]] + [b[0] for b in blocks]
            ref_price = np.repeat(refs, n-1)[:len(price[:, i])]

            stop_price = rolling_extreme * (1 - type[i] * bps[i] / 10000) + pct[i] * (rolling_extreme - ref_price)

            mask = price[:, i] < stop_price
            masks.append(mask)

        return np.logical_or.reduce(masks)
    
add_stop('my_stop_rules.var_dynamic', VarDynamicStop)