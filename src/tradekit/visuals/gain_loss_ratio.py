"""This module provides the gain_loss_ratio function.

It plots the ratio :math:`\frac{gains_only}{losses_only}` as a pie chart.
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import pandas as pd

def gain_loss_ratio(blotter: pd.Series, ax: Axes = None) -> Axes:
    """This function creates a pie chart for the gain/loss ratio.

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
    gains = blotter['gain_loss_ratio']
    gain_pct = blotter['gains_only'] / (blotter['gains_only'] - blotter['losses_only'])
    loss_pct = 1 - gain_pct

    # Colors (green = wins, red = losses)
    colors = ["#139c4c", "#c3392a"]

    # Doughnut chart
    ax.pie(
        [gain_pct, loss_pct],
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops=dict(width=0.35, edgecolor="white")
    )

    # Center percentage text
    ax.text(
        0, 0,
        f"{gains:.2f}",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#2ecc71"
    )

    # Title
    ax.set_title("Gain/Loss Ratio", pad=10)

    # Keep it circular
    ax.set_aspect("equal")

    return ax