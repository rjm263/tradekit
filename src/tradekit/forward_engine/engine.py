"""This module provides the ForwardEngine class.

This is the main module for live trading. It can be used in combination with a supervisor (see :class:`~tradekit.supervisor.supervisor.Supervisor`). It takes a strategy, various trading rules (stop-loss, take-profit and various date/time, macro event and asset volume restrictions) and notifier class (see :class:`~tradekit.notifiers.base.Notifier`) as inputs. The output is a data frame containing the basic trading data for each trade executed.
"""

from tradekit.strategies.base import Strategy
from tradekit.strategies.factory import load_strategy
from tradekit.data.feed import MarketFeed
from tradekit.data.buffer import MarketBuffer
from tradekit.forward_engine.trade import Trade
from tradekit.notifiers.base import Notifier
from tradekit.notifiers.events import Event
import numpy as np
import pandas as pd
import time
import os
import pickle
import json
import signal
import threading
import logging

class ForwardEngine:
    """This class provides an engine for live trading strategies.
    """
    def __init__(self, name: str, strategy: Strategy, notifiers: list[Notifier] | None = None) -> None:
        """Initialises a ForwardEngine object.

        Parameters
        ----------
        name : str
            Name of the engine; relevant if used in combination with a supervisor
        strategy : Strategy
            The strategy class to be tested (see :class:`~tradekit.strategies.base.Strategy`)
        notifiers : list[Notifier] | None, optional
            The notifiers used to notify once a trade was exited, by default None
        """       
        self.name = name
        self.strategy = strategy
        self.feed = MarketFeed(strategy.symbols, strategy.interval, strategy.window)
        self.buffer = MarketBuffer(strategy.window)
        self.notifiers = notifiers
        self.active_trades: dict[int, Trade] = {}
        self.closed_trades: list[dict] = []
        self._shutdown = threading.Event()
        self._shutdown_reason = None
        self._logger = logging.getLogger(__name__)
        self._log_path = None
        self._eval_path = None

    # =============================== EVAL ON SINGLE BAR ===============================

    def _on_bar(self, ts: pd.Timestamp, bar: pd.Series) -> None: 
        """Checks for entry signals and violations of trading restrictions, given current bar.

        Parameters
        ----------
        ts : pd.Timestamp
            The time stamp of the current bar
        bar : pd.Series
            The current bar containing price data (OHLC) and volume
        """        
        # update active trades and buffer by new market bar
        self._update_trades(ts, bar) 
        self.buffer.update(bar)
        
        # check for new signals triggered by current bar; if there are, open trades
        signals = self.strategy.on_bar(ts, bar, self.buffer.to_df()) 
        for _, signal_row in signals.iterrows(): 
            self._open_trade(signal_row, bar)

    def _open_trade(self, signal_row: pd.Series, bar: pd.Series) -> None:
        """Opens new trade based on a signal.

        Parameters
        ----------
        signal_row : pd.Series
            The signal triggering entry of a trade; it contains the following info:
            
            - symbols 
            - trade_type 
            - capital 
            - entry_ts 
            - timeout
        bar : pd.Series
            The current bar containing price data (OHLC) and volume
        """        
        tt = signal_row.trade_type

        # instatiate new Trade object with trade details
        trade = Trade(
            symbols=signal_row.symbols,
            trade_id=self.name + "_" + str(signal_row.name),
            trade_type=tt if isinstance(tt, np.ndarray) else np.array(tt),
            trade_capital=signal_row.capital,
            entry_ts=signal_row.entry_ts,
            entry_price=bar['Close'].values,
            entry_vol=bar['Volume'].values,
            stop_rule=self.strategy.stop_rule,
            profit_rule=self.strategy.profit_rule,
            date_rules=self.strategy.date_rules,
            vol_rules=self.strategy.vol_rules,
            event_rules=self.strategy.event_rules,
            timeout=signal_row.timeout,
        )

        # add new trade to active trades registry
        self.active_trades[signal_row.name] = trade
        self._logger.info(f' Opened trade:\n{trade.to_state()}\n')

    def _update_trades(self, ts: pd.Timestamp, bar: pd.Series) -> None:
        """Upates active trades according to take-profit/stop-loss and trading restrictions.

        Parameters
        ----------
        ts : pd.Timestamp
            The time stamp of he current bar
        bar : pd.Series
            The current bar containing price data (OHLC) and volume
        """        
        for _, trade in self.active_trades.items():
            check, reason = trade.check_exit(ts, bar)
            if check:
                trade.is_open = False
                self._exit_trade(trade, reason, ts, bar)

    def _exit_trade(self, trade: Trade, reason: str, ts: pd.Timestamp, bar: pd.Series) -> None:
        """Exits active trade based on trading rules, saves closed trade and notifies.

        Parameters
        ----------
        trade : Trade
            The active trade to be closed
        reason : str
            The reason for exiting the trade
        ts : pd.Timestamp
            The time stamp of trade exit
        bar : pd.Series
            The current bar containing price data (OHLC) and volume
        """        
        record = {
            'symbols': trade.symbols,
            'signal_id': trade.trade_id,
            'type': trade.trade_type.tolist(),
            'capital': trade.trade_capital.tolist(),
            'entry_time': trade.entry_ts.isoformat(),
            'exit_time': ts.isoformat(),
            'entry_price': trade.entry_price.tolist(),
            'exit_price': bar['Close'].values,
            'exit_reason': reason
        }

        # add closed trade to registry
        self.closed_trades.append(record)

        # notify about closed trade via selected notifiers
        if self.notifiers is not None:
            event = Event(type='trade_exit',
                          source=self.name,
                          ts=ts,
                          payload=record)
            
            for notifier in self.notifiers:
                try:
                    notifier.notify(event=event)
                except Exception as e:
                    self._logger.exception(' Notifier failed: {e}\n')

        # append closed trade to json file storing the latter
        if self._eval_path is not None:
            with open(self._eval_path, 'a') as f:
                f.write(json.dumps(record) + '\n')

        # remove closed trade from active trades registry
        del self.active_trades[trade.trade_id]
        self._logger.info(f' Exited trade {trade.trade_id}\n')

    # =============================== PERSISTENCE =================================

    def save_state(self, path: str) -> None:
        """Saves the current engine state to a .pkl file.

        This is necessary for persistence when used together with a supervisor. If the engine crashes, the supervisor will attempt to restart it from this checkpoint file.

        Parameters
        ----------
        path : str
            The path where the checkpoint file is to be stored
        """        
        state = {'strategy': self.strategy.to_state(),
                 'buffer': self.buffer.to_df(),
                 'active_trades': [t.to_state() for t in self.active_trades.values()],
                 'feed_cursor': self.feed.cursor}
        
        # making save_state crash-safe
        tmp_path = f'{path}.tmp'
        with open(tmp_path, 'wb') as f:
            pickle.dump(state, f)
        os.replace(tmp_path, path)

        
    def load_state(self, path: str) -> None:
        """Loads the engine state from a checkpoint .pkl file.

        This is necessary for persistence when used together with a supervisor. If the engine crashes, the supervisor will attempt to restart it from this checkpoint file.

        Parameters
        ----------
        path : str
            The path to the checkpoint file from which the engine is reloaded
        """        
        with open(path, 'rb') as f:
            state = pickle.load(f)

        self.strategy = load_strategy(state['strategy'])
        self.buffer.from_df(state['buffer'])
        self.active_trades = {d['trade_id']: Trade.from_state(d) for d in state['active_trades']}
        self.feed.cursor = state['feed_cursor']

    # =============================== SHUTDOWN LOGIC ===============================

    def _register_shutdown_hooks(self) -> None:
        """Helper that registers shutdown signals.

        This is relevant for use with a supervisor. When the engine crashes, this handles shutdown of the process.
        """        
        def handler(signum, frame):
            self._shutdown_reason = f'signal: {signum}'
            self._shutdown.set()

        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    # =============================== RUN ENGINE ==================================
    
    def _warm_up(self):
        """Fills a buffer with market data as required by the custom strategy.

        This is useful, e.g., for tracking moving averages etc.
        """        
        hist = self.feed.history()

        if hist.empty:
            return

        self.buffer.from_df(hist)
        self.feed.cursor = hist.index[-1]

    def run(self, poll_interval: int=60, check_every: int=10, runtime: str | None=None, 
            checkpoint_path: str='./checkpoint.pkl', log_path: str='./engine.log', eval_path: str='./'):
        """Runs the live trading engine.

        This is the main method of the ForwardEngine class. It polls the feed for new bars, checks whether signals are emitted by the strategy for those bars and, depending on the outcome, opens new trades or exits active trades.

        Parameters
        ----------
        poll_interval : int, optional
            The time interval between consecutive polls, by default 60 (seconds)
        check_every : int, optional
            The amount of polls before a checkpoint is set, by default 10
        runtime : str | None, optional
            The runtime of engine, by default None (i.e. runs until interrupted)
        checkpoint_path : str, optional
            The path at which the .pkl checkpoint file is stored, by default './checkpoint.pkl'
        log_path : str, optional
            The path at which the log file is stored, by default './engine.log'
        eval_path : str, optional
            The path at which the closed trades are stored as a jsonl file, by default './'
        """        
        self._register_shutdown_hooks()
        
        self._log_path = log_path
        logging.basicConfig(filename=self._log_path, encoding='utf-8', level=logging.INFO)
        
        self._eval_path = eval_path + self.name + '_trades.jsonl'
        
        # check whether checkpoint exists and load engine from there
        if os.path.exists(checkpoint_path):
            try:
                self.load_state(checkpoint_path)
                self._logger.info(f' Engine state reloaded from {checkpoint_path}.\n')
            except Exception as e:
                self._logger.info(f' Failed to load state ({e}). Starting fresh...\n')
        else:
            self._logger.info(' Starting from fresh state.\n')

        if len(self.buffer.to_df()) < self.strategy.window:
            self._warm_up()
            self._logger.info(f' Buffer filled with {len(self.buffer.to_df())} bars.\n')

        bar_count = 0
        start_time = pd.Timestamp.now()
        
        # convert runtime from str to pd.Timedelta 
        if runtime is not None:
            runtime = pd.to_timedelta(runtime)

        while not self._shutdown.is_set():
            try:
                if runtime is not None and pd.Timestamp.now() - start_time > runtime:
                    self._shutdown_reason = 'Max runtime exceeded'
                    self._shutdown.set()
                    break

                new_bars = self.feed.poll()

                for ts, bar in new_bars.iterrows():
                    if self._shutdown.is_set():
                        break

                    self._on_bar(ts, bar)
                    bar_count += 1

                    # save checkpoints 
                    if bar_count % check_every == 0:
                        self.save_state(checkpoint_path)

                # sleep until remainder of poll interval has elapsed
                now = time.time()
                sleep_time = poll_interval - (now % poll_interval)
                self._shutdown.wait(timeout=sleep_time)

            except Exception as e:
                self._shutdown_reason = f'exception: {e}'
                self._logger.exception(' Engine crashed\n')
                self._shutdown.set()
                break

        self._logger.info(f' Shutting down ({self._shutdown_reason})...\n')

        self.save_state(checkpoint_path)