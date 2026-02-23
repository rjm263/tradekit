"""This module provides the make_dashboard function.

This function creates a dashboard out of the following plot functions:

- :func:`~tradekit.visuals.gain_loss_ratio.gain_loss_ratio`
- :func:`~tradekit.visuals.market_time.market_time`
- :func:`~tradekit.visuals.performance.performance`
- :func:`~tradekit.visuals.pnl_stats.pnl_stats`
- :func:`~tradekit.visuals.trade_stats.trade_stats`
- :func:`~tradekit.visuals.win_rate.win_rate`
"""

from tradekit.visuals.trade_stats import trade_stats
from tradekit.visuals.gain_loss_ratio import gain_loss_ratio
from tradekit.visuals.market_time import market_time
from tradekit.visuals.performance import performance
from tradekit.visuals.pnl_stats import pnl_stats
from tradekit.visuals.win_rate import win_rate
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd

def make_dashboard(trades: pd.DataFrame, blotter: pd.Series) -> tuple[Figure, Axes]:
    """This function creates a dashboard of plots.

    It uses basic info about closed trades and the output of a :class:`~tradekit.metrics.blotter.TradeBlotter`.

    Parameters
    ----------
    trades : pd.DataFrame
        The data frame containing basic info about closed trades
    blotter : pd.Series
        The trade blotter used to evaluate the closed trades

    Returns
    -------
    tuple[Figure, Axes]
        The figure and axes for the dashboard plot
    """    
    fig = plt.figure(figsize=(18, 10))

    # Layout definition (figure coordinates)
    layout = {
        "trade_stats": [0.02, 0.6, 0.3, 0.45],
        "performance": [0.4, 0.55, 0.55, 0.45],
        "pnl_stats":   [0.02, 0.02,  0.3, 0.5],
        "win_rate": [0.4, 0.02, 0.15, 0.45],
        "gain_loss_ratio": [0.6, 0.02, 0.15, 0.45],
        "market_time": [0.8, 0.02, 0.15, 0.45]
    }

    # Create axes
    axes = {name: fig.add_axes(pos) for name, pos in layout.items()}

    # Call plot functions
    pnl_stats(blotter, axes["pnl_stats"])
    performance(trades, axes["performance"])
    trade_stats(blotter, axes["trade_stats"])
    win_rate(blotter, axes["win_rate"])
    gain_loss_ratio(blotter, axes["gain_loss_ratio"])
    market_time(blotter, axes["market_time"])

    return fig, axes
