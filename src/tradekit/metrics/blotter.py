"""This module provides the TradeBlotter class.

Given a list of closed trades (in form of a data frame or json), the blotter computes several useful trade metrics. These are used, e.g., to create the dashboard in :func:`~tradekit.visuals.dashboard.make_dashboard`.
"""

from tradekit.fees.base import FeeModel
from tradekit.visuals.dashboard import make_dashboard
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import numpy as np

class TradeBlotter:
    """This class produces a trade blotter for a given fee model.
    """    
    def __init__(self, fee_model: FeeModel) -> None:
        """Initialises the TradeBlotter class.

        Parameters
        ----------
        fee_model : FeeModel
            The fee model used to determine PnL and returns
        """        
        self.fees_model = fee_model

    def extend_trades(self, trades: pd.DataFrame) -> pd.DataFrame:
        """Extends basic trade data by PnL and return.

        Parameters
        ----------
        trades : pd.DataFrame
            The data frame of containing basic info about closed trades

        Returns
        -------
        pd.DataFrame
            The extended data frame containing PnL ('pnl') and return ('return')
        """        
        trades_ext = trades.copy()

        trades_ext['pnl'] = (trades_ext['capital'] / trades_ext['entry_price'] * trades_ext['exit_price']
                            - trades_ext['capital']) * trades_ext['type'] - self.fees_model.fees(trades)
        trades_ext['pnl'] = trades_ext['pnl'].map(sum)
        trades_ext['return'] = trades_ext['pnl'] / trades_ext['capital']
        trades_ext['return'] = trades_ext['return'].map(sum)

        return trades_ext

    def from_df(self, trades: pd.DataFrame) -> pd.Series:
        """Computes useful trade metrics, given basic info about closed trades.

        Parameters
        ----------
        trades : pd.DataFrame
            The data frame containing basic info about the closed trades

        Returns
        -------
        pd.Series
            The series containing the following trade metrics:

            - total_trades: the total number of trades executed
            - wins: the number of winning trades
            - losses: the number of loosing trades
            - neutrals: the number of neutral trades (i.e. break-even)
            - timeout_exits: the number of exits due to timeout
            - pnl: the combined PnL of all trades
            - gains_only: the PnL of all winning trades
            - losses_only: the PnL of all loosing trades
            - best_trade: the PnL of the best trade
            - worst_trade: the PnL of the worst trade
            - avg_gain: the average gain per trade
            - avg_loss: the average loss per trade
            - gain_per_trade: the average PnL per trade
            - gain_loss_ratio: the ratio :math:`\frac{gains_only}{losses_only}`
            - win_rate: the rate at which trades are winning :math:`\frac{wins}{total_trades}`
            - max_drawdown: the largest observed decline in the value of an asset from its peak to its
                subsequent lowest point, before a new peak is attained
            - max_runup: the largest observed rise in the value of an asset from its trough to its subsequent highest point, before a new trough is attained
            - volatility: the standard deviation of returns for all trades
            - days_in_market: the total amount of days all trades where active in the market
        """        
        trades_ext = trades.copy()

        trades_ext['pnl'] = (trades_ext['capital'] / trades_ext['entry_price'] * trades_ext['exit_price']
                            - trades_ext['capital']) * trades_ext['type'] - self.fees_model.fees(trades)
        
        if not isinstance(trades_ext['pnl'], float):
            trades_ext['pnl'] = trades_ext['pnl'].map(sum)
            trades_ext['capital'] = trades_ext['capital'].map(sum)
        
        trades_ext['return'] = trades_ext['pnl'] / trades_ext['capital']
        trades_ext['holding_period'] = (trades_ext['exit_time'] - trades_ext['entry_time']).dt.days

        trades_ext['is_win'] = trades_ext['pnl'] > 0
        trades_ext['is_loss'] = trades_ext['pnl'] < 0
        trades_ext['is_neutral'] = trades_ext['pnl'] == 0

        stats_per_cat = trades_ext.groupby('exit_reason')['return'].agg(['count'])

        num_trades = len(trades_ext)
        
        wins = trades_ext['is_win'].sum()
        losses = trades_ext['is_loss'].sum()
        neutrals = trades_ext['is_neutral'].sum()
        
        win_rate = wins / num_trades if num_trades > 0 else np.nan

        total_profit = trades_ext[trades_ext['is_win'] == True]['pnl'].sum()
        total_loss = trades_ext[trades_ext['is_win'] == False]['pnl'].sum()

        pnl = trades_ext['pnl'].sum()

        avg_gain = trades_ext[trades_ext['is_win'] == True]['pnl'].mean()
        avg_loss = trades_ext[trades_ext['is_win'] == False]['pnl'].mean()
        best_trade = trades_ext['pnl'].max()
        worst_trade = trades_ext['pnl'].min()
        gain_per_trade = pnl / num_trades
        
        gain_loss_ratio = total_profit / -total_loss
        
        equity = trades_ext['pnl'].cumsum()

        max_drawdown = _max_drawdown(equity)
        max_runup = _max_runup(equity)

        volatility = trades_ext['return'].std()

        trading_start = trades['entry_time'].min()
        trading_end = trades['exit_time'].max()
        total_days = _market_time((trades['symbols'].iloc[0])[0], trading_start, trading_end)
        trades_ext['days_in_market'] = trades_ext.apply(lambda row: _market_time(row['symbols'][0], row['entry_time'], row['exit_time']), axis=1)
        days_in_market = trades_ext['days_in_market'].sum() / total_days if total_days != 0 else 0
        
        return pd.Series(
            {
                'total_trades': num_trades,
                'wins': wins,
                'losses': losses,
                'neutrals': neutrals,
                'timeout_exits': stats_per_cat.loc['timeout', 'count'] if 'timeout' in stats_per_cat.index else 0, 
                'pnl': pnl,
                'gains_only': total_profit,
                'losses_only': total_loss,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'avg_gain': avg_gain,
                'avg_loss': avg_loss,
                'gain_per_trade': gain_per_trade,
                'gain_loss_ratio': gain_loss_ratio,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'max_runup': max_runup,
                'volatility': volatility,
                'days_in_market': days_in_market
            }
        )

    def from_json(self, path: str) -> pd.Series:
        """Computes a trade blotter from a json file containing closed trades.

        This method simply loads the json content into a data frame and then calls ``from_df``.

        Parameters
        ----------
        path : str
            The path to the json file where all closed trades are listed

        Returns
        -------
        pd.Series
            The output of the trade blotter, see :meth:`TradeBlotter.from_df`
        """        
        trades = pd.read_json(path, lines=True)

        trades['capital'] = trades['capital'].map(np.array)
        trades['entry_price'] = trades['entry_price'].map(np.array)
        trades['exit_price'] = trades['exit_price'].map(np.array)
        trades['type'] = trades['type'].map(np.array)

        return self.from_df(trades)
    
    def get_dashboard(self, df: str | pd.DataFrame, save_to: str | None = None):
        """Creates a dashboard with plots of several useful trade metrics.

        The resulting dashboard contains the following plots:
        
        - trade stats: PnL, gains only, losses only, max drawdown, max runup, number of wins/losses/neutrals
        - PnL stats: average gain/loss, best/worst trade, average PnL per trade
        - trade performance: bar plot where bar height is PnL and x-coord is exit date
        - win percentage: pie chart showing the percentage of winning trades
        - gain/loss ratio: pie chart showing gain/loss ratio
        - market time: pie chart showing the total amount of time all trades where active in the market 

        Parameters
        ----------
        df : str | pd.DataFrame
            The path to json or data frame where all closed trades are stored
        save_to : str | None, optional
            The path where the dashboard plot should be stored, by default None (i.e. won't be saved)
        """        
        if isinstance(df, pd.DataFrame):
            trades = df.copy()
        else:
            trades = pd.read_json(df, lines=True)
            
            trades['capital'] = trades['capital'].map(np.array)
            trades['entry_price'] = trades['entry_price'].map(np.array)
            trades['exit_price'] = trades['exit_price'].map(np.array)
            trades['type'] = trades['type'].map(np.array)
 
        fig, ax = make_dashboard(self.extend_trades(trades), self.from_df(trades))

        if save_to is None:
            plt.show()
        else:
            fig.savefig(save_to, dpi=300, bbox_inches='tight')

        
from tradekit.utils.cals_dict import YFINANCE_TO_MCAL
import pandas_market_calendars as mcal
def _market_time(symb: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.Timedelta:
    exchange = YFINANCE_TO_MCAL[yf.Ticker(symb).info.get('fullExchangeName')]
    cal = mcal.get_calendar(exchange)

    sched = cal.schedule(start_date=start, end_date=end)

    return len(sched)

def _max_drawdown(s: pd.DataFrame):
    running_peak = s.cummax()
    drawdown = (s - running_peak)

    return drawdown.min()

def _max_runup(s: pd.DataFrame):
    running_through = s.cummin()
    runup = (s - running_through)

    return runup.max()
