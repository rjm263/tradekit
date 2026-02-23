"""This module provides the win_rate function.

It plots the win_rate :math:`\\{wins}{total_trades}` as a pie chart.
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import pandas as pd

def win_rate(blotter: pd.Series, ax: Axes = None) -> Axes:
    """This function plots the win rate as a pie chart.

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
    win_pct = blotter['win_rate'] * 100
    lose_pct = 100 - win_pct

    # Colors (green = wins, red = losses)
    colors = ["#139c4c", "#c3392a"]

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
        color="#2ecc71"
    )

    # Title
    ax.set_title("% Winning Trades", pad=10)

    # Keep it circular
    ax.set_aspect("equal")

    return ax