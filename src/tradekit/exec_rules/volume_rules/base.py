"""This module provides the VolumeRule base class.

It is the base class to be used for custom subclasses involving trading volume restrictions.
"""

from abc import ABC, abstractmethod
import numpy as np
import numpy.typing as npt
import pandas as pd

class VolumeRule(ABC):
    """This class provides a base class for trading volume restrictions.
    """
    def __init__(self, entry_vol: npt.NDArray, trade_type: npt.NDArray) -> None:
        """Initialises the VolumeRule class.

        Parameters
        ----------
        entry_vol : npt.NDArray
            The trading volume at entry time
        trade_type : npt.NDArray
            The type of trade (long or short)
        """
        self.entry_vol = entry_vol
        self.trade_type = trade_type
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
    def hit(self, vol: int) -> bool:
        """Checks if the time stamp of the current bar violates volume restrictions.

        Parameters
        ----------
        vol : int
            The volume of the current bar

        Returns
        -------
        bool
            True if the time stamp violates restrictions, False otherwise
        """
        pass

    @abstractmethod
    def exit_mask(self, df: pd.DataFrame) -> npt.NDArray:
        """Creates a boolean mask checking which time stamps violate restrictions.

        Parameters
        ----------
        df : pd.DataFrame
            The data frame containing price data, indexed by datetimes

        Returns
        -------
        npt.NDArray
            The boolean array specifying whether restrictions are violated
        """
        return np.zeros(len(df), dtype=bool)
    
    @abstractmethod
    def update(self, bar: pd.Series) -> None:
        """Updates the volume restrictions imposed, based on current bar.

        This can be useful when min/max volume levels should be changed dynamically.

        Parameters
        ----------
        bar : pd.Series
            The current bar of price data
        """
        pass