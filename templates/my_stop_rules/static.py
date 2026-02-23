from tradekit.exec_rules.stop.base import StopRule
from tradekit.exec_rules.stop.factory import add_stop
import numpy.typing as npt
import numpy as np

class StaticStop(StopRule):
    def __init__(self, entry_price, trade_type, bps: npt.NDArray):
        super().__init__(entry_price, trade_type)
        self.bps = np.atleast_1d(bps)
        self._level = entry_price * (1 - trade_type * bps / 10000)
    
    def hit(self, bar):
        cond = np.where(self.trade_type == 1,
                        self.level >= bar['Low'].values,
                        self.level <= bar['High'].values)
        
        return cond.all()

    def update(self, bar):
        pass

    def exit_mask(self, df) -> npt.NDArray:
        """
        NB: df MUST have the trade entry date as its first line!
            It can not be the price data for the whole period!
        """
        stop_price = self.entry_price * (1 - self.trade_type * self.bps / 10000)

        low = df['Low'].to_numpy()
        high = df['High'].to_numpy()

        masks = []

        for i, p in enumerate(stop_price):
            if self.trade_type[i] == 1:
                mask = low[:, i] < p
            else:
                mask = high[:, i] > p

            masks.append(mask)

        return np.logical_or.reduce(masks)
    
add_stop('my_stop_rules.static', StaticStop)