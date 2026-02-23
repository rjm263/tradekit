"""This module provides the FeeModel base class.

It is the base class to be used for custom subclasses of fee models to be used when evaluating trades (e.g., for PnL).
"""

from abc import ABC, abstractmethod
import pandas as pd

class FeeModel(ABC):
    """This class provides a base class for custom fee models.
    """    
    @abstractmethod
    def fees(df: pd.DataFrame) -> pd.Series:
        """Computes fees based on the class model.

        Parameters
        ----------
        df : pd.DataFrame
            The data frame containing basic trade info, such as entry/exit price, long/short trade

        Returns
        -------
        pd.Series
            The series containing fees, based on the given model, for each trade
        """        
        pass