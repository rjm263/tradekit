"""This module provides the Trade class.

This is a helper class to store info about and monitor active trades.
"""

from dataclasses import dataclass, field
from tradekit.exec_rules.stop.factory import make_stop, load_stop
from tradekit.exec_rules.profit.factory import make_profit, load_profit
from tradekit.exec_rules.volume_rules.factory import make_volume_rule, load_volume_rule
from tradekit.exec_rules.event_rules.factory import make_event_rule
from tradekit.exec_rules.date_rules.factory import make_datetime_rule
import pandas as pd
import numpy as np
import numpy.typing as npt

@dataclass
class Trade:
    """This class provides a way to store and monitor active trades.

    In addition to storing basic data about the active trade, it contains the method ``check_exit`` which checks whether a take-profit or stop-loss was hit and if any trading restrictions are violated.

    Parameters
    ----------
    symbols: list[str]
        The list of symbols involved in the trade
    trade_id: int
        The id of the trade
    trade_type: npt.NDArray[int_]
        The type of the trade (long or short)
    trade_capital: npt.NDArray[np.float64]
        The capital to be invested in the trade
    entry_ts: pd.Timestamp
        The time stamp for the time the trade was entered
    entry_price: npt.NDArray[np.float64]
        The array of entry prices, one for each symbol involved
    entry_vol: npt.NDArray[np.int_]
        The array of traded volumes at entry, one for each symbol
    stop_rule: dict
        The dictionary containing the parameters to instantiate a StopRule class
    pofit_rule: dict
        The dictionary containing the parameters to instantiate a ProfitRule class
    date_rules: list[dict] | None, optional
        The list of dictionaries containing the parameters to instantiate a DatetimeRule class, one for each rule, by default None
    event_rules: list[dict] | None, optional
        The list of dictionaries containing the parameters to instantiate a EventRule class, one for each rule, by default None
    vol_rules: list[dict] | None, optional
        The list of dictionaries containing the parameters to instantiate a VolumeRule class, one for each rule, by default None
    timeout: pd.Timedelta | None, optional
        The amount of time before the trade times out, by default None (i.e. runs until it hits take-profit or stop-loss level)
    is_open: bool, optional
        Specifies whether a trade is considered active or not, by default True
    """    
    symbols: list[str]
    trade_id: int
    trade_type: npt.NDArray[np.int_]
    trade_capital: npt.NDArray[np.float64]

    entry_ts: pd.Timestamp
    entry_price: npt.NDArray[np.float64]
    entry_vol: npt.NDArray[np.int_]

    stop_rule: dict
    profit_rule: dict

    date_rules: list[dict] | None = None
    vol_rules: list[dict] | None = None
    event_rules: list[dict] | None = None

    timeout: pd.Timedelta | None = None

    is_open: bool = True

    stop: object = field(init=False)
    profit: object = field(init=False)
    dates: list[object] = field(init=False)
    vols: list[object] = field(init=False)
    events: list[object] = field(init=False)

    def __post_init__(self) -> None:
        """Instatiated stop, profit and trading restriction classes from dicts.
        """        
        price_args = {'entry_price': self.entry_price, 'trade_type': self.trade_type}
        vol_args = {'entry_vol': self.entry_vol, 'trade_type': self.trade_type}
        
        self.stop = make_stop(price_args | self.stop_rule)
        self.profit = make_profit(price_args | self.profit_rule)

        self.vols = [make_volume_rule(vol_args | d) for d in (self.vol_rules or [])]
        self.dates = [make_datetime_rule(d) for d in (self.date_rules or [])]
        self.events = [make_event_rule(d) for d in (self.event_rules or [])]
            

    def to_state(self) -> dict:
        """Serialises a class instance to a dictionary.

        Returns
        -------
        dict
            The dictionary containing the class attributes
        """        
        return {"symbols": self.symbols,
                "trade_id": self.trade_id,
                "trade_type": self.trade_type,
                "trade_capital": self.trade_capital,
                "entry_ts": self.entry_ts,
                "entry_price": self.entry_price,
                "entry_vol": self.entry_vol,
                "stop_rule": self.stop_rule,
                "profit_rule": self.profit_rule,
                "date_rules": self.date_rules,
                "vol_rules": self.vol_rules,
                "event_rules": self.event_rules,
                "timeout": self.timeout,
                "stop_state": self.stop.to_state(),
                "profit_state": self.profit.to_state(),
                "vol_state": [v.to_state() for v in self.vols],
                "is_open": self.is_open}

    @classmethod
    def from_state(cls, d: dict) -> Trade:
        """Loads a Trade object from a state dictionary.

        Parameters
        ----------
        d : dict
            The state dictionary containing all state attributes

        Returns
        -------
        Trade
            The Trade object loaded from the state dictionary
        """        
        trade = cls(symbols=d["symbols"],
                    trade_id=d["trade_id"],
                    trade_type=d["trade_type"],
                    trade_capital=d["trade_capital"],
                    entry_ts=d["entry_ts"],
                    entry_price=d["entry_price"],
                    entry_vol=d["entry_vol"],
                    stop_rule=d["stop_rule"],
                    profit_rule=d["profit_rule"],
                    date_rules=d["date_rules"],
                    vol_rules=d["vol_rules"],
                    event_rules=d["event_rules"],
                    timeout=d["timeout"])
        
        # perform post-init 
        trade.stop = load_stop(d['stop_state'])
        trade.profit = load_profit(d['profit_state'])

        trade.events = [make_event_rule(di) for di in d['event_rules']]
        trade.dates = [make_datetime_rule(di) for di in d['date_rules']]
        trade.vols = [load_volume_rule(di) for di in d['vol_state']]
        
        trade.is_open = d['is_open']

        return trade

    def check_exit(self, ts: pd.Timestamp, bar: pd.Series) -> tuple[bool, str | None]:
        """Checks if current bar hits take-profit/stop-loss price level and trading restrictions.

        Parameters
        ----------
        ts : pd.Timestamp
            The time stamp of the current bar
        bar : pd.Series
            The current bar containing price data (OHLC) and volume

        Returns
        -------
        tuple[bool, str | None]
            The first entry determines whether price level was hit or trading restriction was violated; the second specifies the reason for the exit (if the first is True)
        """        
        # if not open, close!
        if not self.is_open:
            return False, None
        
        # update stop/profit exit prices and trading restrictions
        self.stop.update(bar)
        self.profit.update(bar)

        self.dates.update(bar)
        self.events.update(bar)
        self.vols.update(bar)

        # timeout is hit if timeout interval has elapsed since entry time
        if self.timeout is not None and self.entry_ts + self.timeout < ts:
            return True, 'timeout'
        
        # check if any date/time restrictions are violated
        if not all(d.hit(ts) for d in self.dates):
            return False, None
        
        # check if any volume restrictions are violated
        if not all(v.hit(vol) for v in self.vols for vol in bar['Volume'].values):
            return False, None
        
        # check if any event restrictions are violated
        if not all(e.hit(ts) for e in self.events):
            return False, None
        
        # check if the stop exit price was hit
        if self.stop.hit(bar):
            return True, 'stop'
        
        # check if the profit exit price was hit
        if self.profit.hit(bar):
            return True, 'profit'
        
        return False, None