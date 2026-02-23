from tradekit.exec_rules.volume_rules.base import VolumeRule
from tradekit.exec_rules.volume_rules.factory import add_volume_rule
import numpy as np

class VolumeInterval(VolumeRule):
    def __init__(self, entry_vol, trade_type, intervals: list[tuple[int, int]] | tuple[int, int]):
        super().__init__(entry_vol, trade_type)
        if isinstance(intervals, tuple):
            intervals = [intervals]

        for s, e in intervals:
            if s > e:
                raise ValueError(f'Interval ({s}, {e}) not valid')

        self.intervals = intervals

    def hit(self, vol):
        """
        True if volume within interval, else False
        """
        if any([s <= vol <= e for s, e in self.intervals]):
            return True
        
        return False
    
    def exit_mask(self, df):
        """
        True if volume within interval, else False
        """
        v = df['Volume'].to_numpy()
        
        masks = []

        for i in range(v.shape[1]):
            mask = np.zeros(len(v), dtype=bool)

            for s, e in self.intervals:
                mask |= (v[:, i] >= s) & (v[:, i] <= e)

            masks.append(mask)

        return np.logical_and.reduce(masks)
    
    def update(self, bar):
        pass
    
add_volume_rule('my_volume_rules.interval', VolumeInterval)