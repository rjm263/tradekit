"""This module provides the BacktestEngine class.

This is the main module for backtesting. It can be used in combination with a supervisor (see :class:`~tradekit.supervisor.supervisor.Supervisor`). It takes a strategy, various trading rules (stop-loss, take-profit and various date/time, macro event and asset volume restrictions) and a backtesting lookback period as inputs. The output is a data frame containing the basic trading data for each trade executed.
"""

from tradekit.strategies.base import Strategy
from tradekit.data.feed import MarketFeed
from tradekit.exec_rules.stop.factory import make_stop
from tradekit.exec_rules.profit.factory import make_profit
from tradekit.exec_rules.date_rules.factory import make_datetime_rule
from tradekit.exec_rules.date_rules.base import DatetimeRule
from tradekit.exec_rules.event_rules.factory import make_event_rule
from tradekit.exec_rules.event_rules.base import EventRule
from tradekit.exec_rules.volume_rules.factory import make_volume_rule
from multiprocessing import Pool, cpu_count
from itertools import chain
import pandas as pd
import numpy as np
import threading
import logging
import signal


class BacktestEngine:
    """This class provides an engine for backtesting strategies.
    """
    def __init__(self, name: str, strategy: Strategy) -> None:
        """Initialises a BacktestEngine object.

        Parameters
        ----------
        name : str
            Name of the engine; relevant if used in combination with a supervisor
        strategy : Strategy
            The strategy class to be tested (see :class:`~tradekit.strategies.base.Strategy`)
        """
        self.name = name
        self.strategy = strategy
        self.feed = MarketFeed(
            symbols=strategy.symbols,
            interval=strategy.interval,
            window=strategy.window
        )
        self.dates = [make_datetime_rule(d) for d in (strategy.date_rules or [])]
        self.events = [make_event_rule(d) for d in (strategy.event_rules or [])]

        self._shutdown = threading.Event()
        self._shutdown_reason = None
        self._logger = logging.getLogger(__name__)
        self._log_path = None
        self._eval_path = None

        _MD = None
        _STRATEGY = None
        _RULES = None
    

    def _register_shutdown_hooks(self) -> None:
        """Necessary for usage with a supervisor. Declares how shutdown signals are handled.
        """
        def handler(signum, frame):
            self._shutdown_reason = f'signal: {signum}'
            self._shutdown.set()

        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
    
    @staticmethod
    def _validate_signal(signal: pd.DataFrame) -> None:
        """Helper function checking that all necessary input is provided by signal dataframe.

        Parameters
        ----------
        signal : pd.DataFrame
            The data frame containing signals emitted by the strategy

        Raises
        ------
        ValueError
            Missing columns in signal data frame
        TypeError
            entry_ts is not datetime-like
        """
        required = {'symbols', 'trade_type', 'capital', 'entry_ts', 'timeout'}
        missing = required - set(signal.columns)
        if missing:
            raise ValueError(f'Missing columns {missing}')
        
        if not pd.api.types.is_datetime64_any_dtype(signal['entry_ts']):
            raise TypeError("entry_ts must be datetime-like")

    @staticmethod
    def _init_worker(md: pd.DataFrame, strategy: Strategy, rules: tuple[list[DatetimeRule], list[EventRule]]) -> None:
        """Initialises market data, strategy and trading rules as provided by strategy.

        Parameters
        ----------
        md : pd.DataFrame
            The data frame containing price data; must contain OHLC and Volume columns
        strategy : Strategy
            The strategy class to be tested (see :class:`~tradekit.strategies.base.Strategy`)
        rules : tuple[list[DatetimeRule], list[EventRule]]
            The trading restrictions involving dates/times and macro events (e.g. earnings)
        """
        BacktestEngine._MD = md
        BacktestEngine._STRATEGY = strategy
        BacktestEngine._RULES = rules

    @staticmethod
    def execute_trade_worker(signal_row: pd.Series) -> dict:
        """Executes a single trade based on a signal emitted by the strategy. Used in :meth:`BacktestEngine.run`.

        Parameters
        ----------
        signal_row : pd.Series
            The signal emitted by the strategy; must contain following columns: 

            - symbols 
            - trade_type 
            - capital 
            - entry_ts 
            - timeout

        Returns
        -------
        dict
            - signal_id
            - symbols
            - type
            - capital
            - entry_time
            - exit_time
            - entry_price
            - exit_price
            - exit_reason

        Raises
        ------
        ValueError
            if no price data is available for the entry date
        ValueError
            if the timeout window is too short
        """
        # retrieve basic data necessary for backtest
        market_data = BacktestEngine._MD
        strategy = BacktestEngine._STRATEGY
        dates, events = BacktestEngine._RULES

        start_ts = signal_row.entry_ts

        if start_ts not in market_data.index:
            raise ValueError('No price data available for entry date')

        price_df = market_data[['Open', 'High', 'Low', 'Close', 'Volume']]
        timestamps = price_df.index

        entry_iloc = timestamps.get_loc(start_ts)
        entry_price = price_df['Close'].iloc[entry_iloc]
        entry_vol = price_df['Volume'].iloc[entry_iloc]

        # build stop and profit classes necessary for trade exit
        price_args = {'entry_price': entry_price, 'trade_type': signal_row.trade_type}
        vol_args = {'entry_vol': entry_vol, 'trade_type': signal_row.trade_type}
        
        stop = make_stop(price_args | strategy.stop_rule)
        profit = make_profit(price_args | strategy.profit_rule)
        vols = [make_volume_rule(vol_args | d) for d in (strategy.vol_rules or [])]

        # if timeout was provided, use it; otherwise set timeout as most recent date available
        if signal_row.timeout is None:
            timeout_ts = timestamps[-1]
        else:
            timeout_ts = start_ts + signal_row.timeout
        timeout_iloc = timestamps.searchsorted(timeout_ts, side='left')
        if timeout_iloc >= len(price_df):
            timeout_iloc = len(price_df) - 1

        # trim market data to period between trade entry and timeout date
        price_after_entry = price_df.iloc[entry_iloc+1:timeout_iloc+1]
        if price_after_entry.empty:
            raise ValueError('Timeout window is too short!')

        # create date/event/vol and stop/profit masks to enforce resp. rules
        list_of_masks = [r.exit_mask(price_after_entry) for r in chain(dates, events, vols)]
        rules_mask = np.logical_and.reduce(list_of_masks)
        
        stop_hit = stop.exit_mask(price_after_entry) & rules_mask
        profit_hit = profit.exit_mask(price_after_entry) & rules_mask
        
        exit_mask = stop_hit | profit_hit

        # identify first date returning True as exit date and record exit reason
        if exit_mask.any():
            exit_delta = exit_mask.argmax()
            exit_iloc = entry_iloc + exit_delta + 1

            if stop_hit[exit_delta]:
                exit_reason = 'stop'
            if profit_hit[exit_delta]:
                exit_reason = 'profit'

        else:
            exit_reason = 'timeout'
            exit_iloc = timeout_iloc

        # Exit at bar close price (can be changed to touch price or next bar open price)
        exit_price = price_df['Close'].iloc[exit_iloc].item()

        return {'signal_id': signal_row.name,
                'symbols': signal_row.symbols,
                'type': signal_row.trade_type,
                'capital': signal_row.capital,
                'entry_time': start_ts,
                'exit_time': timestamps[exit_iloc],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'exit_reason': exit_reason}

    def run(self, period: str, eval_path: str | None = None, log_path: str | None = None) -> pd.DataFrame:
        """Runs many :meth:`BcktestEngine.execute_trade_worker` processes in parallel.

        Parameters
        ----------
        period : str
            The lookback period for the backtest (e.g. '1mo', '3mo', '1y')
        eval_path : str | None, optional
            The path where closed trades are stored as a jsonl file, by default None
        log_path : str | None, optional
            The path where a log file is stored when used with a supervisor, by default None

        Returns
        -------
        pd.DataFrame
            Data frame which contains the following basic trade data columns:
            
            - signal_id
            - symbols
            - type
            - capital
            - entry_time
            - exit_time
            - entry_price
            - exit_price
            - exit_reason

        Raises
        ------
        ValueError
            if there are no signals emitted by the strategy for the chosen lookback period
        """
        # initialise shutdown hooks (for use w/ supervisor), log and eval paths, market data
        self._register_shutdown_hooks()
        
        self._log_path = log_path
        logging.basicConfig(filename=self._log_path, encoding='utf-8', level=logging.INFO)

        self._eval_path = eval_path + self.name + '_trades.jsonl' if eval_path is not None else None

        market_data = self.feed.history(period=period)

        # create df of trading signals, either using signals method or, 
        # if not provided in the resp. strategy class, by iterating through the market data 
        # and checking for signal via on_bar
        if hasattr(self.strategy, 'signals') and callable(getattr(self.strategy, 'signals')):
            signals = self.strategy.signals(market_data)
            self._logger.info(" Using signals-method for vectorized computation")
        else:
            sigs = []
            for ts, bar in market_data.iterrows():
                sigs.append(self.strategy.on_bar(ts, bar, market_data.loc[:ts]))
            signals = pd.concat(sigs) if sigs else pd.DataFrame()
            self._logger.info(" No signals-method provided; using bar-by-bar computation")

        if signals.empty:
            self._shutdown.set()
            raise ValueError('There are no signals for the chosen period')
        else:
            BacktestEngine._validate_signal(signals)

        # parallel execution of trades initiated by signals, using execute_trade_worker; 
        # initialise market data, strategy and trading rules via _init_worker
        try: 
            with Pool(
                cpu_count(),
                initializer=BacktestEngine._init_worker,
                initargs=(market_data, self.strategy, (self.dates, self.events))
            ) as pool:
                results = pool.map(
                    BacktestEngine.execute_trade_worker,
                    (row for _, row in signals.iterrows())
                )
            
            trades = pd.DataFrame(results)

            if self._eval_path is not None:
                trades.to_json(self._eval_path, orient='records', lines=True)
                self._logger.info(f" Saving output to file {self._eval_path}")

            return trades
        
        except Exception as e:
            self._shutdown_reason = f'exception: {e}'
            self._logger.exception(' Engine crashed\n')
            self._shutdown.set()

        self._logger.info(f' Shutting down ({self._shutdown_reason})...\n')