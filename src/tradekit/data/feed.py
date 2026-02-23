"""This module provides the MarketFeed class.

It creates a market feed with price data for a custom choice of symbols, bar intervals and lookback window. The market data is obtain from Yahoo Finance via the `yfinance <https://pypi.org/project/yfinance/>`_ package.
"""

import yfinance as yf
import pandas as pd

class MarketFeed:
    """
    Class used to retrive market data from Yahoo Finance (via yfinance package)

    Arguments:
    - symbols: str | list[str]
        list of symbols for which market data should be retrieved
    - interval: str
        time interval between any two trading bars (e.g. '1m', '1h', '1d');
        default is one minute ('1m')
    - window: int
        number of entries given the interval spacing; default is 30
    """
    def __init__(self, symbols: str | list[str], interval: str='1m', window: int=30):
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.interval = interval
        self.period = _window_to_period(interval, window)
        self._last_ts = None

    @property
    def cursor(self):
        return self._last_ts
    
    @cursor.setter
    def cursor(self, c):
        c = pd.Timestamp(c).tz_convert('UTC') if c.tzinfo else pd.Timestamp(c, tz='UTC')
        self._last_ts = c

    def history(self, interval=None, period=None):
        """
        Retrieves historic data

        Arguments:
        - interval: str
            in case an interval deviating from initialisation parameter is needed; default is None
        - period: str
            lookback period (e.g. '1mo', '1y', '5y'); default is None and window is used
        """
        if interval is None:
            interval = self.interval
        if period is None:
            period = self.period
            
        df = yf.download(self.symbols,
                            interval=interval,
                            period=period,
                            progress=False,
                            auto_adjust=True
                            )
        
        if df is None:
            raise MarketDataError(f'yfinance failed for {self.symbols}')

        return df.iloc[:-1]
        

    def poll(self):
        """
        Polls latest market data (given interval, window provided) and returns 
        most recent entries not yet returned in earlier polls
        """
        df = yf.download(self.symbols,
                            interval=self.interval,
                            period=self.period,
                            progress=False,
                            auto_adjust=True
                            )
            
        if df is None:
            raise MarketDataError(f'yfinance failed for {self.symbols}')

        df = df[~df.index.duplicated(keep='last')]
        df = df.iloc[:-1]
        
        if self._last_ts is not None:
            df = df[df.index > self._last_ts]

        if not df.empty:
            self._last_ts = df.index[-1]

        return df
    

class MarketDataError(Exception):
    pass


def _window_to_period(interval: str, window: int) -> str:
    """
    Convert interval + window to yfinance period string,
    accounting for actual market hours.
    """
    minutes_per_day = 390
    hours_per_day = 6.5
    if interval[-1] == 'm':
        bars_per_day = -(minutes_per_day // -int(interval[:-1]))
    elif interval[-1] == 'h':
        bars_per_day = -int(hours_per_day // -int(interval[:-1]))
    elif interval[-1] == 'd':
        bars_per_day = 1
    else:
        raise ValueError(f'Interval {interval} is not supported')
    
    days_needed = -(window // -bars_per_day)

    if days_needed <= 1:
        return '2d'
    else:
        return f'{days_needed + 1}d'
    # NB: if we call yf with period='1d' before market close, it only
    # provides current days market data (i.e. <= full market day's worth
    # of bars). In order to have at least #window bars, need to add extra day 