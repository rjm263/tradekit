from tradekit.exec_rules.date_rules.base import DatetimeRule
from tradekit.exec_rules.date_rules.factory import add_datetime_rule

class DayRule(DatetimeRule):
    def __init__(self, days_to_exclude: list[int] | int):
        self.days = days_to_exclude if isinstance(days_to_exclude, list) else [days_to_exclude]

    def hit(self, ts):
        """
        False if date is hit, else True
        """
        if ts.weekday in self.days:
            return False
        
        return True
    
    def exit_mask(self, df):
        """
        False if date is hit, else True
        """
        return ~df.index.weekday.isin(self.days)
    
    def update(self, bar):
        pass
    
add_datetime_rule('my_date_rules.day', DayRule)
    
    