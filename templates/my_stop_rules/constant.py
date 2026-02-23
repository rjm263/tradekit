from tradekit.exec_rules.stop.base import StopRule
from tradekit.exec_rules.stop.factory import add_stop

import numpy as np

class ConstantStop(StopRule):
    def __init__(self, entry_price, trade_type, abs_diff: float):
        super().__init__(entry_price, trade_type)
        self.abs_diff = abs_diff
        self._level = entry_price - abs_diff

    def hit(self, bar):
        cond = np.where(self.trade_type == 1,
                        self.level >= bar['Low'].values,
                        self.level <= bar['High'].values)
        
        return cond.all()
    
    def update(self, bar):
        pass

    def exit_mask(self, df):
        price = df['Close'].to_numpy()
        stop_price = self.entry_price - self.trade_type * self.abs_diff

        masks = []

        for i in range(len(self.trade_type)):
            if self.trade_type[i] == 1:
                mask = price[:, i] < stop_price[i]
            else:
                mask = price[:, i] > stop_price[i]
            
            masks.append(mask)

        return np.logical_or.reduce(masks)

add_stop('my_stop_rules.constant', ConstantStop)