"""This module provides the EventRule base class.

It is the base class to be used for custom subclasses involving trading restrictions vis-a-vis macro events.
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import numpy.typing as npt

class EventRule(ABC):
    """This class provides a base class for trading restrictions vis-a-vis macro events.
    """
    @abstractmethod
    def hit(self, ts: pd.Timestamp) -> bool:
        """Checks if the time stamp of the current bar violates event restrictions.

        Parameters
        ----------
        ts : pd.Timestamp
            The time stamp of the current bar

        Returns
        -------
        bool
            True if the time stamp violates restrictions, False otherwise
        """
        pass

    @staticmethod
    def exit_mask(df: pd.DataFrame) -> npt.NDArray:
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
        """Updates the event restrictions imposed, based on current bar.

        Parameters
        ----------
        bar : pd.Series
            The current bar of price data
        """
        pass