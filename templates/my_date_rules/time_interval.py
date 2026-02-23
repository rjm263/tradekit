from tradekit.exec_rules.date_rules.base import DatetimeRule
from tradekit.exec_rules.date_rules.factory import add_datetime_rule
from datetime import datetime
import numpy as np

class TimeIntervalRule(DatetimeRule):
    def __init__(self, intervals: list[tuple[str, str]] | tuple[str, str]):
        if isinstance(intervals, tuple):
            intervals = [intervals]

        time_tuples = [(datetime.strptime(s, '%H:%M:%S').time(), datetime.strptime(e, '%H:%M:%S').time()) for s, e in intervals]

        for s, e in time_tuples:
            if s > e:
                raise ValueError(f'Interval ({s}, {e}) not valid')

        self.intervals = time_tuples

    def hit(self, ts):
        """
        False if date is hit, else True
        """
        t = ts.time()

        for s, e in self.intervals:
            if s <= e:
                if s <= t <= e:
                    return False
            else:
                if s <= t or t <= e:
                    return False
        
        return True
    
    def exit_mask(self, df):
        """
        False if date is hit, else True
        """
        t = df.index.time
        mask = np.zeros(len(t), dtype=bool)

        for s, e in self.intervals:
            if s <= e:
                mask |= (t >= s) & (t <= e)
            else:
                mask |= (t >= s) | (t <= e)

        return mask
    
    def update(self, bar):
        pass
    
add_datetime_rule('my_date_rules.time_interval', TimeIntervalRule)
