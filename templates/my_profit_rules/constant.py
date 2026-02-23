from tradekit.exec_rules.profit.base import ProfitRule
from tradekit.exec_rules.profit.factory import add_profit

import numpy as np
import numpy.typing as npt

class ConstantProfit(ProfitRule):
    def __init__(self, entry_price, trade_type, abs_diff: npt.NDArray):
        super().__init__(entry_price, trade_type)
        self.abs_diff = np.atleast_1d(abs_diff)
        self._level = entry_price + abs_diff
    
    def hit(self, bar):
        cond = np.where(self.trade_type == 1,
                        self.level <= bar['High'].values,
                        self.level >= bar['Low'].values)
        
        return cond.all()
    
    def update(self, bar):
        pass

    def exit_mask(self, df):
        price = df['Close'].to_numpy()
        profit_price = self.entry_price + self.trade_type * self.abs_diff
        type = self.trade_type

        masks = []

        for i in range(len(type)):
            if type[i] == 1:
                mask = price[:, i] >= profit_price[i]
            else:
                mask = price[:, i] <= profit_price[i]

            masks.append(mask)

        return np.logical_or.reduce(masks)

add_profit('my_profit_rules.constant', ConstantProfit)