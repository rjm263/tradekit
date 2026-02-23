"""This module provides the performance function.

It plots the PnL of each trade over the datetime the trade was exited.
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import MaxNLocator
import pandas as pd

def performance(blotter: pd.DataFrame, ax: Axes = None) -> Axes:
    """This function creates a bar plot of trade PnLs.

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
        fig, ax = plt.subplots()

    # Data
    dates = blotter['exit_time'].dt.tz_localize(None)
    values = blotter['pnl']

    # Colors: green for gains, red for losses
    colors = ["#139c4c" if v >= 0 else "#c3392a" for v in values]

    # Bars
    ax.bar(dates, values, width=2, color=colors, edgecolor="black", linewidth=0.3)

    # Zero line
    ax.axhline(0, color="black", linewidth=1)

    # X-axis formatting
    ax.xaxis.set_major_locator(MaxNLocator(10))

    # Y-axis formatting
    ymax = blotter["pnl"].max() + 10
    ymin = blotter["pnl"].min() - 10
    ax.set_ylabel("Gains")
    ax.set_ylim(ymin, ymax)

    # Grid (light, like the screenshot)
    ax.grid(axis="y", linestyle="-", alpha=0.3)
    ax.set_axisbelow(True)

    # Cosmetic tweaks
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_title("Gross Performance", pad=10)

    return ax
