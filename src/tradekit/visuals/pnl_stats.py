"""This module provides the pnl_stats function.

It plots the following PnL stats:
- average gain
- average loss
- best trade PnL
- worst trade PnL
- average PnL per trade
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import seaborn as sns
import pandas as pd

def pnl_stats(blotter: pd.Series, ax: Axes = None) -> Axes:
    """This function creates a bar chart of PnLs.

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
    avg_gain = blotter['avg_gain']
    best_trade = blotter['best_trade']

    avg_loss = blotter['avg_loss']
    worst_trade = blotter['worst_trade']

    avg_per_trade = blotter['gain_per_trade']

    x_gain = -.2
    x_loss = .2
    bar_width = 0.4

    # --- Gain side ---
    # Background (best trade)
    ax.bar(
        x_gain,
        best_trade,
        width=bar_width,
        color="#a9dfbf",  # light green
        zorder=1
    )

    # Foreground (average gain)
    ax.bar(
        x_gain,
        avg_gain,
        width=bar_width,
        color="#139c4c",  # dark green
        zorder=2
    )

    # --- Loss side ---
    # Background (worst trade)
    ax.bar(
        x_loss,
        worst_trade,
        width=bar_width,
        color="#f5b7b1",  # light red
        zorder=1
    )

    # Foreground (average loss)
    ax.bar(
        x_loss,
        avg_loss,
        width=bar_width,
        color="#c3392a",  # dark red
        zorder=2
    )

    # Zero line
    ax.axhline(0, color="black", linewidth=1)

    # Text annotations
    ax.text(
        x_gain, 
        avg_gain / 2, 
        f"Average\n{avg_gain:.2f}",
        ha="center", 
        va="center", 
        color="white", 
        fontsize=12, 
        fontweight="bold"
    )

    ax.text(
        x_loss, 
        avg_loss / 2, 
        f"Average\n{avg_loss:.2f}",
        ha="center", 
        va="center", 
        color="white", 
        fontsize=12, 
        fontweight="bold"
    )

    ax.annotate(
        f"Gain of best trade: {best_trade:.2f}",
        xy=(x_gain, best_trade),
        xytext=(0, 6),              
        textcoords="offset points",
        ha="center",
        va="bottom",
        color="#139c4c",
        fontsize=12,
        fontweight="bold"
    )

    ax.annotate(
        f"Loss of worst trade: {worst_trade:.2f}",
        xy=(x_loss, worst_trade),
        xytext=(0, -6),
        textcoords="offset points",
        ha="center",
        va="top",
        color="#c3392a",
        fontsize=12,
        fontweight="bold"
    )

    title_color = "#139c4c" if avg_per_trade >= 0 else "#c3392a"

    # Title
    ax.set_title(f"avg: {avg_per_trade:.2f} per trade", color=title_color, fontsize=14, weight="bold", pad=30)

    # Cleanup
    ax.set_xticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    sns.despine(left=True, bottom=True)

    # Remove y-axis completely
    ax.get_yaxis().set_visible(False)
    ax.spines["left"].set_visible(False)

    return ax
