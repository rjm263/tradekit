import yfinance as yf
import pandas as pd
from tradekit.exec_rules.event_rules.factory import add_event_rule
from tradekit.exec_rules.event_rules.base import EventRule

class Earnings(EventRule):
    def __init__(self, symbols: str | list[str]):
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
    
    def hit(self, ts) -> bool:
        """
        False if earnings event hit, else True
        """
        cal = yf.Calendars().get_earnings_calendar()
        sym_earnings = cal[cal['Company'].index.isin(self.symbols)]
        dates = sym_earnings['Event Start Date'].to_list()

        if ts.date() in [d.date() for d in dates]:
            return False
        
        return True
    
    def exit_mask(self, df):
        """
        False if earnings event hit, else True
        """
        start = df.index[0]
        end = df.index[-1]
        limit = (end.year - start.year + 1) * 4

        all_earnings = []

        for t in self.symbols:
            earnings = yf.Ticker(t).get_earnings_dates(limit=limit)
            if earnings is None:
                earnings = pd.DataFrame()
            else:
                earnings = earnings.reset_index()
                earnings = earnings[
                    (earnings['Earnings Date'] >= start) & 
                    (earnings['Earnings Date'] <= end)
                ]
            all_earnings.append(earnings)
        
        dates = pd.concat(all_earnings)
        if not dates.empty:
            dates = dates['Earnings Date'].dt.tz_convert("UTC").to_list()

        return ~df.index.floor('D').isin(dates)
    
    def update(self, bar):
        pass


add_event_rule('my_event_rules.earnings', Earnings)