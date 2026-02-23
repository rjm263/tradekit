"""This module provides the market_time function.

It plots the total time all trades where active in the market.
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import pandas as pd

def market_time(blotter: pd.Series, ax: Axes = None) -> Axes:
    """This function creates a pie chart for the market time.

    Parameters
    ----------
    blotter : pd.Series
        The output of a :class:`~tradekit.metrics.blotter.TradeBlotter`
    ax : Axes, optional
        The axes into which the plot should be integrated, by default None

    Returns
    -------
    Axes
        The axes for the pie chart plot
    """    
    if ax is None:
        fig, ax = plt.subplots(figsize=(3,3))

    # Data
    pct_in_market = blotter["days_in_market"]
    win_pct = 100 * pct_in_market if pct_in_market <= 1  else 100
    lose_pct = 100 - win_pct

    # Colors
    colors = ["#1e3cd0", "#dbdbdb"]

    # Doughnut chart
    ax.pie(
        [win_pct, lose_pct],
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops=dict(width=0.35, edgecolor="white")
    )

    # Center percentage text
    ax.text(
        0, 0,
        f"{win_pct:.2f}%",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#1e3cd0"
    )

    # Title
    ax.set_title("Time in Market", pad=10)

    # Keep it circular
    ax.set_aspect("equal")

    return ax