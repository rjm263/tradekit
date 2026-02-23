"""This module provides the class MarketBuffer. 

It creates a buffer of price data of custom length which can be updated after new bars are emitted. This is useful, e.g., when using moving averages.
"""

from collections import deque
import pandas as pd

class MarketBuffer:
    """This class provides a buffer which collects individual bars of price data.
    """
    def __init__(self, window: int) -> None:
        """Initialises the MarketBuffer class.

        Parameters
        ----------
        window : int
            The length of the buffer to be created
        """
        self.window = window
        self._bars = deque(maxlen=window)

    def update(self, bar: pd.Series) -> None:
        """Updates the buffer by deleting the oldest and appending the newest bar.

        Parameters
        ----------
        bar : pd.Series
            The latest bar of price data to be added to the buffer
        """
        self._bars.append(bar)

    def to_df(self) -> pd.DataFrame:
        """Generates a data frame from the buffer.

        Returns
        -------
        pd.DataFrame
            The curret buffer given as a data frame
        """
        if not self._bars:
            return pd.DataFrame()
        return pd.DataFrame(self._bars)
    
    def from_df(self, df: pd.DataFrame) -> None:
        """Loads a buffer from a data frame.

        Parameters
        ----------
        df : pd.DataFrame
            The data frame to be loaded into the buffer
        """
        for ts, bar in df.iterrows():
            self.update(bar) 