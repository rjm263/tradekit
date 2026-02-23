"""This module provides the Strategy base class.

It is used as the parent class for custom strategy classes, which are to be used either by the :class:`~tradekit.backtest_engine.engine.BacktestEngine` or the :class:`~tradekit.forward_engine.engine.ForwardEngine`.
"""

import pandas as pd
import numpy.typing as npt
import numpy as np

from abc import ABC, abstractmethod
class Strategy(ABC):
    """The class used as parent for custom strategy classes.
    """    
    def __init__(self,
            symbols: str | list[str], 
            capital: float | list[float],
            stop_rule: dict, 
            profit_rule: dict, 
            interval: str = '1m', 
            window: int = 30,
            date_rules: list[dict] | None = None,
            event_rules: list[dict] | None = None,
            vol_rules: list[dict] | None = None,
            timeout: str = None
    ) -> None:
        """Initialises the Strategy class.

        Parameters
        ----------
        symbols : str | list[str]
            The symbols involved in the strategy
        capital : float | list[float]
            The capital to be invested in each trade resulting from the strategy
        stop_rule : dict
            The dictionary necessary to instantiate a StopRule object; this provides a stop-loss price level
        profit_rule : dict
            The dictionary necessary to instantiate a ProfitRule object; this provides a take-profit price level
        interval : str, optional
            The time interval between consecutive bars ('m' for minute, 'h' for hour, 'd' for day, 'mo' for month, 'y' for year), by default '1m'
        window : int, optional
            The length of the buffer filled with historic data necessary for signal generation (in units of intervals), by default 30
        date_rules : list[dict] | None, optional
            The list of dictionaries from which a list of :class:`~tradekit.exec_rules.date_rules.base.DatetimeRule` object will be created; these provide trading restrictions based on dates/times, by default None
        event_rules : list[dict] | None, optional
            The list of dictionaries from which a list of :class:`~tradekit.exec_rules.event_rules.base.EventRule` objects will be created; these provide trading restrictions based on macro events, by default None
        vol_rules : list[dict] | None, optional
            The list of dictionaries from which a list of :class:`~tradekit.exec_rules.volume_rules.base.VolumeRule` objects will be created; these provide trading restrictions based on traded volumes, by default None
        timeout : str, optional
            The timeout to be used per trade ('m' for minute, 'h' for hour, 'd' for day, 'mo' for month, 'y' for year), by default None (i.e. runs until interrupted)
        """        
        self._symbols = symbols if isinstance(symbols, list) else [symbols]
        self._capital = np.array(capital) if isinstance(capital, list) else np.array([capital])
        self._interval = interval
        self._window = window
        self.stop_rule = stop_rule
        self.profit_rule = profit_rule
        self.date_rules = date_rules
        self.event_rules = event_rules
        self.vol_rules = vol_rules
        self.timeout = pd.to_timedelta(timeout) if timeout is not None else None

    @property
    def symbols(self):
        return self._symbols
    @symbols.setter
    def symbols(self, s):
        self._symbols = s if isinstance(s, list) else [s]

    @property
    def capital(self):
        return self._capital
    @capital.setter
    def capital(self, c):
        self._capital = c if isinstance(c, npt.NDArray) else np.array([c])
    
    @property
    def interval(self):
        return self._interval
    @interval.setter
    def interval(self, i):
        self._interval = i

    @property
    def window(self):
        return self._window
    @window.setter
    def window(self, w):
        self._window = w 

    def to_state(self) -> dict:
        """Serialises a Strategy object to a dictionary.

        This is used for checkpointing during engine runs.

        Returns
        -------
        dict
            The dictionary containing all attributes of the current state of the Strategy object
        """        
        return {'name': self.__class__.__name__, **self.__dict__}

    @abstractmethod
    def on_bar(self, ts: pd.Timestamp, bar: pd.Series, history: pd.DataFrame) -> pd.DataFrame:
        """Checks if a signal should be emitted based on current bar.

        Parameters
        ----------
        ts : pd.Timestamp
            The time stamp of the current bar
        bar : pd.Series
            The current bar containing price data (OHLC) and volume
        history : pd.DataFrame
            The historic data used to compute relevant indicators

        Returns
        -------
        pd.DataFrame
            The signal emitted by the strategy; it contains the following:
            
            - symbols: the list of symbols involved in the strategy
            - trade_type: +1/-1 for long/short trade
            - capital: the capital to be invested in the trade
            - entry_ts: the entry time of the trade
            - timeout: the time the trade is allowed to be active before closing
        """        
        pass