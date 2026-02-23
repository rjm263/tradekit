from tradekit.exec_rules.profit.base import ProfitRule
from tradekit.exec_rules.profit.factory import add_profit
import numpy.typing as npt
import numpy as np

class StaticProfit(ProfitRule):
    def __init__(self, entry_price, trade_type, bps: int | list[int]):
        super().__init__(entry_price, trade_type)
        self.bps = np.atleast_1d(bps)
        self._level = entry_price * (1 + trade_type * bps / 10000)

    def hit(self, bar):
        cond = np.where(self.trade_type == 1,
                        self.level <= bar['High'].values,
                        self.level >= bar['Low'].values)
        
        return cond.all()

    def update(self, bar):
        pass

    def exit_mask(self, df):
        profit_price = self.entry_price * (1 + self.trade_type * self.bps / 10000)
        type = self.trade_type

        high = df['High'].to_numpy()
        low = df['Low'].to_numpy()

        masks = []

        for i, p in enumerate(profit_price):
            if type[i] == 1:
                mask = high[:, i] >= p
            else:
                mask = low[:, i] <= p

            masks.append(mask)

        return np.logical_or.reduce(masks)

add_profit('my_profit_rules.static', StaticProfit)

