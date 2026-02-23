"""This module provides the trade_stats function.

It plots cards of the following trading stats:
- total number of trades
- number of winning trades
- number of neutral trades
- number of loosing trades
- number of timeouts 
- PnL
- gains only
-losses only
- max drawdown
- max runup
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import matplotlib.patches as patches
import pandas as pd

def trade_stats(blotter: pd.Series, ax: Axes = None) -> Axes:
    """This function plots various trade statistics.

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

    # --- Left card area (50% width, full height) ---
    left_x0, left_x1 = 0.0, 0.48  # fraction of axis width
    y_top, y_bottom = 0.95, 0.05  # fraction of axis height

    # Draw left card background
    ax.add_patch(
        patches.Rectangle(
            (left_x0, y_bottom), left_x1-left_x0, y_top-y_bottom,
            transform=ax.transAxes, color="white", zorder=0
        )
    )

    # Left title bar
    ax.add_patch(
        patches.Rectangle(
            (left_x0, y_top-0.05*(y_top-y_bottom)), left_x1-left_x0, 0.05*(y_top-y_bottom),
            transform=ax.transAxes, color="#d9d9d9", zorder=1
        )
    )
    ax.text(left_x0+0.02, y_top-0.03*(y_top-y_bottom), "Trade Distribution",
            ha="left", va="center", fontsize=11, fontweight="bold", zorder=2)

    # Left text (aligned at colons)
    labels = ["Total", "Winning", "Neutral", "Losing", "Timeouts"]
    values = [blotter['total_trades'], blotter['wins'], blotter['neutrals'],
                blotter['losses'], blotter['timeout_exits']]
    colors = ["black", "#139c4c", "black", "#c3392a", "black"]
    n_lines = len(labels)

    for i, (label, value, c) in enumerate(zip(labels, values, colors)):
        y_pos = y_top - 0.15 - i*0.15*(y_top-y_bottom)
        ax.text(left_x0+0.48*0.48, y_pos, f"{label}:", color=c, ha='right', va='center', fontsize=14, fontweight='bold', transform=ax.transAxes)
        ax.text(left_x0+0.52*0.48, y_pos, f"{value:.0f}", color=c, ha='left', va='center', fontsize=14, transform=ax.transAxes)

    # Left card border
    ax.add_patch(
        patches.Rectangle(
            (left_x0, y_bottom), left_x1-left_x0, y_top-y_bottom,
            transform=ax.transAxes, fill=False, edgecolor='black', linewidth=1.5, zorder=3
        )
    )

    # --- Right vertical cards ---
    right_x0, right_x1 = 0.52, 0.98
    n_cards = 5
    card_height = (y_top - y_bottom) / n_cards

    pnl_colors = ["#139c4c", "#d5f1e0"] if blotter['pnl'] >= 0 else ["#c3392a", "#f6dad7"]

    card_titles = ["PnL", "Gains Only", "Losses Only", "Max Drawdown", "Max Runup"]
    card_values = [blotter['pnl'], blotter['gains_only'], blotter['losses_only'], blotter['max_drawdown'], blotter['max_runup']]
    text_colors = [pnl_colors[0], "#139c4c", "#c3392a", "#c3392a", "#139c4c"]
    face_colors = [pnl_colors[1], "#d5f1e0", "#f6dad7", "#f6dad7", "#d5f1e0"]

    for i in range(n_cards):
        y0 = y_top - (i + 1) * card_height
        y1 = y_top - i * card_height
        
        # Card background
        ax.add_patch(
            patches.Rectangle(
                (right_x0, y0), right_x1-right_x0, card_height,
                transform=ax.transAxes, color=face_colors[i], zorder=0
            )
        )
        
        # Title bar (gray)
        ax.add_patch(
            patches.Rectangle(
                (right_x0, y1-0.25*card_height), right_x1-right_x0, 0.25*card_height,
                transform=ax.transAxes, color="#d9d9d9", zorder=1
            )
        )
        ax.text(right_x0+0.02, y1-0.15*card_height, card_titles[i],
                ha="left", va="center", fontsize=11, fontweight="bold", zorder=2, transform=ax.transAxes)
        
        # Main value
        ax.text((right_x0+right_x1)/2, y0+0.4*card_height, f"{card_values[i]:.2f}",
                color=text_colors[i], ha="center", va="center", fontsize=14, zorder=2, transform=ax.transAxes)
        
        # Black border
        ax.add_patch(
            patches.Rectangle(
                (right_x0, y0), right_x1-right_x0, card_height,
                transform=ax.transAxes, fill=False, edgecolor='black', linewidth=1.5, zorder=3
            )
        )

    ax.axis('off')

    return ax