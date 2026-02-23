"""This module provides the ProfitRule base class.

It is the base class to be used for custom subclasses involving take-profit exits.
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import numpy.typing as npt


class ProfitRule(ABC):
    """This class provides a base class for take-profit exits.
    """    
    def __init__(self, entry_price: npt.NDArray, trade_type: npt.NDArray) -> None:
        """Initialises the ProfitRule class.

        Parameters
        ----------
        entry_price : npt.NDArray
            The asset price at the time the trade is entered
        trade_type : npt.NDArray
            The type of trade executed (long or short)
        """        
        self.entry_price = np.atleast_1d(entry_price)
        self.trade_type = np.atleast_1d(trade_type)
        self._level = None

    @property
    def level(self) -> float:
        return self._level
    @level.setter
    def level(self, l):
        self._level = l

    def to_state(self) -> dict:
        """Serialises a class instance to a dictionary.

        Returns
        -------
        dict
            The class attributes
        """  
        return {'name': self.__class__.__name__, **self.__dict__}
    
    @abstractmethod
    def hit(self, bar: pd.Series) -> bool:
        """Checks if the current bar triggers a take-profit exit.

        Parameters
        ----------
        bar : pd.Series
            The current bar containing market price (OHLC) and volume

        Returns
        -------
        bool
            True if the current price is above the take-profit price level, False otherwise
        """
        pass

    @abstractmethod
    def exit_mask(self, df: pd.DataFrame) -> npt.NDArray:
        """Creates a boolean mask checking which prices are above the take-profit price level.

        Parameters
        ----------
        df : pd.DataFrame
            The data frame containing OHLC and volumes for the lookback period, indexed by datetimes

        Returns
        -------
        npt.NDArray
            The boolean array specifying which prices are above take-profit price levels
        """        
        pass

    @abstractmethod
    def update(self, bar: pd.Series) -> None:
        """Updates the take-profit price level, based on current bar.

        Parameters
        ----------
        bar : pd.Series
            The current bar containing market price (OHLC) and volume
        """        
        pass