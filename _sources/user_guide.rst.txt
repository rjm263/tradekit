User Guide
==========

The main philosophy of this package is a separation of signal emission, trade execution and evaluation. While execution and evaluation are handled entirely by the package, for signal emission the user has to input their own code. As such, the package itself does not contain any pre-made strategies, nor does it contain any rules for trading or fee models to be used for evaluation (however, some templates are provided at `Templates <templates.html>`_).

The idea is for the user to add their custom strategies etc. to dedicated package registries, which are accessed by two kinds of engine: 

- `ForwardEngine <tradekit.forward_engine.html>`_ for live trading and 
- `BacktestEngine <tradekit.backtest_engine.html>`_ for backtesting strategies

Once added to the registry, a strategy can be tested by configuring and running the respective engine, either locally or on an external server. For the latter, the package provides the `Supervisor <tradekit.supervisor.html>`_ class.

The full workflow of coding a strategy, testing it with an engine, running the engine on a server, and evaluating the strategy is explained below. For the sample code, we assume the following file structure::

    project/
    ├── my_strategies/
    │   ├── __init__.py
    │   └── ma_crossover.py
    ├── my_profit_rules/
    │   └── __init__.py
    │   └── static.py
    ├── my_stop_rules/
    │   └── __init__.py
    │   └── dynamic.py
    ├── my_event_rules/
    │   └── __init__.py
    │   └── earnings.py
    ├── ma_config.json
    ├── ma_engine.py
    └── ma_supervisor.py

Step 1: Creating Strategies
---------------------------

In this section, the term *strategy* collectively means

- a rule for emission of buy/sell signals based on some technicals (support for fundamentals will be added soon)
- a rule for take-profit exits 
- a rule for stop-loss exits

as well as an optional set of additional rules about closing trades

- on specific days or times during the day
- on days on which macro events happen 
- when assets are traded at specified volumes

For each item above there exists a base class in the package and a dedicated registry. Any custom implementations **must** be subclasses of the former (and as such contain certain essential methods) and added to the latter.

Strategy
^^^^^^^^

The base class for the main part of the strategy---signal emission---is the `Strategy <tradekit.strategies.html>`_ class. It is imported via 

.. code-block:: python 
    
    from tradekit.strategies.base import Strategy

For custom signal emission, the user must code their strategy into a subclass thereof. In particular, they need to provide the following methods:

- ``Strategy.on_bar(ts, bar, history)``

    This method checks for every bar (containing price data and volumes) whether a signal is emitted according to the user's strategy or not. The ``history`` argument provides historic data used to compute the technicals on which the strategy is based. 

- ``Strategy.signals(df)``, optional

    This method is optional but highly recommended to implement. Its purpose is to vectorise signal emission for backtesting: given historical data ``df``, it should create a list of signals.
    If this method is not provided, the signals for backtesting will be obtained by checking every single for signal emission via ``on_bar`` (which significantly increases the runtime). 

A custom ``Strategy`` class, named ``TestClass`` and provided in 'test/class/location/test_class.py', is added to the registry by appending the command

.. code-block:: python
    
    add_strategy(test.class.location.test_class, TestClass)``

to the test_class.py file.

Note that all subsequent items listed (profit, stop etc.) must be included as arguments in the custom ``Strategy`` class (in the form of dicts containing the kwargs to initialise a respective object).

.. A sample implementation for a basic moving average crossover is provided in `ma_crossover.py <../../../templates/my_strategies/ma_crossover.py>`_.

Here is a sample implementation `ma_crossover <../../../templates/my_strategies/ma_crossover.py>`_ for a moving average crossover strategy (note that this code is *very* basic and takes rather long since it uses ``pandas`` for computing MAs; for faster code use numpy):

.. code-block:: python

    from tradekit.strategies.base import Strategy
    from tradekit.strategies.factory import add_strategy
    from tradekit.exec_rules.date_rules.factory import make_datetime_rule
    from tradekit.exec_rules.event_rules.factory import make_event_rule
    from tradekit.exec_rules.volume_rules.factory import make_volume_rule
    import pandas as pd
    import numpy as np

    class MACrossover(Strategy):
        def __init__(self,
                symbols, 
                capital, 
                interval, 
                stop_rule, 
                profit_rule, 
                date_rules, 
                event_rules, 
                vol_rules,
                timeout,
                fast: int, 
                slow: int 
        ):
            super().__init__(
                symbols=symbols,
                capital=capital,
                interval=interval,
                stop_rule=stop_rule,
                profit_rule=profit_rule,
                date_rules=date_rules,
                event_rules=event_rules,
                vol_rules=vol_rules,
                timeout=timeout
            )
            self.fast = fast
            self.slow = slow
            self._window = slow + 1
            self.sign = None
            self.id = 0

            self.dates = [make_datetime_rule(d) for d in (date_rules or [])]
            self.events = [make_event_rule(d) for d in (event_rules or [])]

        # Creates a buy signal if fast MA of closing price crosses over slow one and buy signal if vice versa
        def on_bar(self, ts, bar, history):
            df = self._add_indicators(history.iloc[-self._window:])
            signal = self._create_signals(df).iloc[-1]

            if signal.enter_long:
                self.id += 1
                type = 1
            elif signal.enter_short:
                self.id += 1
                type = -1
            else:
                return pd.DataFrame()

            # Check if current bar is embargoed by datetime or event restrictions
            if all(e.hit(ts) for e in self.events) and all(d.hit(ts) for d in self.dates):
                vol_args = {'entry_vol': bar['Volume'].values, 'trade_type': type}
                vols = [make_volume_rule(vol_args | d) for d in (self.vol_rules or [])]

                # Check if current bar is embargoed by volume restrictions
                if all(v.hit(vol) for v in vols for vol in bar['Volume'].values):
                    return self._build_trade(ts, type)

            return pd.DataFrame()
        
        def signals(self, df):
            full_df = self._add_indicators(df)
            sigs = self._create_signals(full_df)

            mask = sigs['enter_long'].values | sigs['enter_short'].values
            entries = full_df[mask].copy()
            entries['type'] = np.where(entries['enter_long'], 1, -1)

            rows = []

            for ts, entry in entries.iterrows():
                # Check if current bar is embargoed by datetime or event restrictions
                if all(e.hit(ts) for e in self.events) and all(d.hit(ts) for d in self.dates):
                    vol_args = {'entry_vol': entry['Volume'].values, 'trade_type': entry['type']}
                    vols = [make_volume_rule(vol_args | d) for d in (self.vol_rules or [])]

                    # Check if current bar is embargoed by volume restrictions
                    if all(v.hit(vol) for v in vols for vol in entry['Volume'].values):
                        self.id += 1
                        rows.append(self._build_trade(ts, entry['type']))

            return pd.concat(rows) if rows else pd.DataFrame()
        
        def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
            df['slow_ma'] = df['Close'].rolling(window=self.slow).mean()
            df['fast_ma'] = df['Close'].rolling(window=self.fast).mean()

            return df
        
        def _create_signals(self, df) -> pd.DataFrame:
            diff = df['fast_ma'] - df['slow_ma']

            sign = np.sign(diff)

            df['sign'] = sign
            df['sign_prev'] = sign.shift(1)

            df['enter_long'] = (df['sign'] == 1) & (df['sign_prev'] <= 0)
            df['enter_short'] = (df['sign'] == -1) & (df['sign_prev'] >= 0)

            return df[['enter_long', 'enter_short']]
        
        def _build_trade(self, ts, type):
            row = {
                'symbols': self.symbols,
                'trade_type': type,
                'capital': self.capital,
                'entry_ts': ts,
                'timeout': self.timeout
            } 

            return pd.DataFrame([row], index=[self.id])


    add_strategy('my_strategies.ma_crossover', MACrossover)           
         
 
        

Profit Exit
^^^^^^^^^^^

The base class for implementing take-profit exits from a trade is the `ProfitRule <tradekit.exec_rules.profit.html>`_ class.
It is imported via

.. code-block:: python

    from tradekit.exec_rules.profit.base import ProfitRule

For custom take-profit exits, the user must code it as a subclass thereof. In particular, they need to provide the following methods:

- ``ProfitRule.hit(bar)``

    This method checks for every ``bar`` whether the take-profit price level was hit or not and returns the corresponding boolean value.

- ``ProfitRule.update(bar)``

    This method is used for updating the take-profit price level according to the current (and historic) asset price. It enables a dynamic exit price.

- ``ProfitRule.exit_mask(df)``

    This method is used to determine take-profit exits in a vectorised way for backtesting. Given historical data ``df``, it determines all bars that would have triggered an exit.

A custom ``ProfitRule`` class, named ``TestProfit`` and provided in 'test/class/location/test_profit.py', is added to the registry by appending the command

.. code-block:: python 
    
    add_profit(test.class.location.test_profit, TestProfit)

to the test_profit.py file.

A sample implementation for a static price level is provided in `static.py <../../../templates/my_profit_rules/static.py>`_.


Stop Exit
^^^^^^^^^

The base class for implementing stop-loss exits from a trade is the `StopRule <tradekit.exec_rules.stop.html>`_ class. It is imported via

.. code-block:: python

    from tradekit.exec_rules.stop.base import StopRule

It is built analogously to the ``ProfitRule`` class above---simply replace 'Profit' by 'Stop' everywhere.

.. A sample implementation for a dynamic price level is provided in `dynamic.py <../../../templates/my_stop_rules/dynamic.py>`_.

Here is a sample implementation `dynamic.py <../../../templates/my_stop_rules/dynamic.py>`_ for a dynamic price level:

.. code-block:: python

    from tradekit.exec_rules.stop.base import StopRule
    from tradekit.exec_rules.stop.factory import add_stop
    import numpy.typing as npt
    import numpy as np
    import pandas as pd
    from collections import deque

    class DynamicStop(StopRule):
        def __init__(self, entry_price, trade_type, bps: npt.NDArray, window: npt.NDArray):
            super().__init__(entry_price, trade_type)
            self.bps = np.atleast_1d(bps)
            self.window = np.atleast_1d(window)
            self._level = entry_price * (1 - trade_type * bps / 10000)
            self.buffer = deque()

        # This method is useful for checkpointing
        def to_state(self) -> dict:
            return {'entry_price': self.entry_price,
                    'trade_type': self.trade_type,
                    'bps': self.bps,
                    'window': self.window,
                    'level': self.level,
                    'buffer': self.buffer}
        
        # Returns True if current low is below exit level (long) or current high is above exit level (short)
        def hit(self, bar):
            cond = np.where(self.trade_type == 1,
                        self.level >= bar['Low'].values,
                        self.level <= bar['High'].values)
            
            return cond.all()

        # Adjusts the exit level dynamically after an interval of len(self.buffer)-many bars by replacing the entry level with the maximum price reached during that interval
        def update(self, bar: pd.Series):
            self.buffer.append(bar['Close'].values)
            if len(self.buffer) >= self.window:
                if self.trade_type == 1:
                    new_price = np.maximum(self.buffer)
                else:
                    new_price = np.minimum(self.buffer)
                self._level = new_price * (1 - self.trade_type * self.bps / 10000)
                self.buffer.clear()

        # Creates a boolean array with entries True if price crosses below exit level and False otherwise (for long positions; vice versa for shorts)
        def exit_mask(self, df) -> npt.NDArray:
            n = self.window
            type = self.trade_type
            bps = self.bps
            entry_price = self.entry_price

            masks = []

            for i in range(len(type)):
                if type[i] == 1:
                    price = df['Low'].to_numpy()
                    blocks = np.lib.stride_tricks.sliding_window_view(price[:, i], n)[::n-1]
                    
                    extremes = [entry_price[i]] + [b.max() for b in blocks]
                else:
                    price = df['High'].to_numpy()
                    blocks = np.lib.stride_tricks.sliding_window_view(price[:, i], n)[::n-1]
                    
                    extremes = [entry_price[i]] + [b.min() for b in blocks]
                
                rolling_extreme = np.repeat(extremes, n-1)[:len(price[:, i])]
                stop_price = rolling_extreme * (1 - type[i] * bps[i] / 10000)

                mask = price[:, i] < stop_price
                masks.append(mask)

            return np.logical_or.reduce(masks)

            
    add_stop('my_stop_rules.dynamic', DynamicStop)
        

        

Datetime Restrictions
^^^^^^^^^^^^^^^^^^^^^

The base class for implementing restrictions on the days and times the engine is allowed to trade is the `DatetimeRule <tradekit.exec_rules.date_rules.html>`_ class. It is imported via

.. code-block:: python

    from tradekit.exec_rules.date_rules.base import DatetimeRule

For custom datetime restrictions, the user must code them as a subclass thereof. In particular, they need to provide the following methods:

- ``DatetimeRule.hit(ts)``

    This method checks for every time stamp ``ts`` whether it is embargoed according to the datetime rule or not. If it is, the return value is ``False``, otherwise it is ``True``

- ``DatetimeRule.update(bar)``

    This method is used for updating the datetime rule over time.

- ``DatetimeRule.exit_mask(df)``

    This method is a vectorised counterpart of ``hit(ts)`` used for backtesting. Given historical data ``df``, it determines all bars that would be embargoed by the datetime rule.

A custom ``DatetimeRule`` class, named ``TestDate`` and provided in 'test/class/location/test_date.py', is added to the registry by appending the command

.. code-block:: python 
    
    add_datetime_rule(test.class.location.test_date, TestDate)

to the test_date.py file.

A sample implementation for banning certain days from trading is provided in `day.py <../../../templates/my_date_rules/day.py>`_.


Event Restrictions
^^^^^^^^^^^^^^^^^^

The base class for implementing restrictions on the days the engine is allowed to trade due macro-economic events is the `EventRule <tradekit.exec_rules.event_rules.html>`_ class. It is imported via 

.. code-block:: python

    from tradekit.exec_rules.event_rules.base import EventRule

It is built analogously to the ``DatetimeRule`` class above---simply replace 'Datetime' by 'Event' everywhere.

A sample implementation for banning days when earnings reports are released from trading is provided in `earnings.py <../../../templates/my_event_rules/earnings.py>`_.


Volume Restrictions
^^^^^^^^^^^^^^^^^^^

The base class for implementing trading restrictions on the engine based on traded volumes is the `VolumeRule <tradekit.exec_rules.volume_rules.html>`_ class. It is imported via 

.. code-block:: python

    from tradekit.exec_rules.volume_rules.base import VolumeRule

It is built analogously to the ``DatetimeRule`` class above---simply replace 'Datetime' by 'Volume' everywhere.

A sample implementation for banning the engine from trading when volumes are outside a given interval is provided in `interval.py <../../../templates/my_volume_rules/interval.py>`_.



Step 2: Configuring the Engine
------------------------------

Say, we want to test our strategy in live trading. For this purpose choose the ``ForwardEngine``. In order to instantiate it, the user needs to provide the following init parameters:

- a name for the ``ForwardEngine`` instance; relevant when multiple engines are used concurrently
- a ``Strategy`` class to be used for signal emission
- a (list of) ``Notifier`` class (see Step 3) to be used for notifying about closed trades

Once a object ``test_engine`` has been instantiated, the engine can be run by calling ``test_engine.run(args)`` with the following set of arguments:

- ``poll_interval`` specifying the time interval between consecutive polls for price data
- ``check_every`` specifying the frequency of setting checkpoints (in units of polling intervals)
- ``runtime`` limits the total runime of the engine
- ``checkpoint_path`` specifying the path to store the checkpoint file at
- ``log_path`` specifying the path to store the log file at
- ``eval_path`` specifying the path to store the jsonl file listing closed trades at

A sample engine is given below (the content of 'ma_engine.py' in the file tree above), using the MA strategy from above on Apple stock. First, we instantiate the ``MACrossover`` class, choosing 20 bars for fast MA and 60 bars for slow MA. For take-profit and stop-loss exits we choose a static price level 350 bps above, resp. 50 bps below entry price. 

.. code-block:: python

    import tradekit as tk

    # Instantiate the MACrossover class for Apple stock with chosen fast and slow MA
    ma_strategy = MACrossover(
        symbols = 'AAPL',
        capital = 1000,
        interval = '1m',
        stop_rule = {
            "name": "my_stop_rules.static", 
            "bps": 50
        },
        profit_rule = {
            "name": "my_profit_rules.static", 
            "bps": 350
        },
        event_rules = [
            {
                "name": "my_event_rules.earnings", 
                "symbols": "AAPL"
            }
        ],
        timeout = '5d',
        fast = 20,
        slow = 60
    )

    # Instantiate the ForwardEngine class for the given strategy
    ma_engine = tk.ForwardEngine(
        name = 'MA_AAPL',
        strategy = ma_strategy
    )

    # Run the engine with a poll interval of 60sec, setting checkpoints every 20 polls, with runtime of 90 days
    ma_engine.run(
        poll_interval = 60,
        check_every = 20,
        runtime = '90d'
    )

After an engine finished running, the closed trades are saved to a jsonl file named '{engine_name}_trades.jsonl', which is stored in the same directory as the engine config file. For the example above, the file is 'MA_AAPL_trades.jsonl'. This file lists basic info about each trade and is used to evaluate the strategy, e.g. by using the `TradeBlotter <tradekit.metrics.html>`_ class.


Step 3: Using a Supervisor
--------------------------

If a strategy is to be tested over a long period of time, it is often not feasible to run the engine locally. Instead, it should be run on an external server. To facilitate this, the package includes the `Supervisor <tradekit.suervisor.html>`_ class. It can orchestrate multiple engines, handle engine crashes savely, and notify the user once engines have finished running.

When using engines with a supervisor, the engine class is not instantiated manually. Instead, the user creates a json config file for the engine object to be run. A sample config file (named 'ma_config.json' in the file tree above) for backtesting the ``MACrossover`` strategy from above on a ``BacktestEngine`` remotely is pasted below:

.. code-block:: json

    {
        "name": "MA_AAPL",
        "strategy": {
            "name": "my_strategies.ma_crossover", 
            "symbols": "AAPL", 
            "interval": "1h", 
            "fast": 20, 
            "slow": 60, 
            "capital": 1000,
            "stop_rule": {
                "name": "my_stop_rules.static", 
                "bps": 50
            },
            "profit_rule": {
                "name": "my_profit_rules.static", 
                "bps": 350
            },
            "date_rules": [
                {
                    "name": "my_date_rules.day", 
                    "days_to_exclude": [4]
                },
                {
                    "name": "my_date_rules.time_interval", 
                    "intervals": [["12:00:00", "15:30:00"]]
                }
            ],
            "event_rules": [
                {
                    "name": "my_event_rules.earnings", 
                    "symbols": "AAPL"
                }
            ],
            "vol_rules": [
                {
                    "name": "my_volume_rules.interval", 
                    "intervals": [[1, 60592490863]]
                }
            ],
            "timeout": "5d"
        },
        "poll_interval": 60,
        "check_every": 10,
        "runtime": "5m",
        "check_path": "./checkpoint.pkl",
        "log_path": "./engine.log",
        "eval_path": "./",
        "fees": {
            "name": "my_fees.broker_a", 
            "bps": 25, 
            "flat": 5
        },
        "period": "9mo"
    }

In order to instantiate a ``Supervisor`` object, the user needs to provide the following init parameters:

- ``backtesting`` specifies whether the supervised engines are for backtesting or live trading
- ``name`` specifies the name of the supervisor; relevant when multiple supervisors are being used
- ``engine_cfgs`` is a dictionary containing the names of all engines as keys and the paths to their configuration files 
    as values
- ``notifiers`` specifies a list of notifiers used to inform the user about crashes, finished runs etc. 

Say, we save the config file above as ``ma_aapl.json`` in the project folder. Then the engine can be run via a supervisor with the following code (the content of 'ma_supervisor.py' in the file tree above):

.. code-block:: python

    import tradekit as tk

    # Instantiate an email notifier to be used by the supervisor
    email_notifier = te.EmailNotifier(
        smtp_host='mail.gmail.com',
        smtp_port=465,
        user='john.doe@gmail.com',
        smtp_password="SMTP_PASSWORD",
        sender='john.doe@gmail.com',
        recipients=['jane.doe@icloud.com', 'lisa.simpson@gmail.com']
    )

    # Instantiate the supervisor, using the BacktestEngine cfg and email_notifier
    ma_supervisor = tk.Supervisor(
        backtesting = True,
        name = "MA_AAPL_supervisor",
        engine_cfgs = {
            "MA_AAPL": "ma_aapl.json"
        },
        notifiers = [email_notifier]
    )

    # Run the supervisor
    ma_supervisor.run()

In the code above we have instantiated an `EmailNotifier <tradekit.notifiers.html>`_ class, which sends an email to the specified recipients, e.g., once an engine finished running.

NB: Currently, this is the only way to get notified. Future versions will include additional types of notification (text messages, signal, slack etc.). 


Step 4: Evaluation
------------------

When a supervisor is used to run the engines and a ``Notifier`` is configured, the notification about a finished run will always include a dashboard of relevant trade metrics as a summary. All plots that are part of the dashboard can be created individually as well, see `visuals <tradekit.visuals.html>`_. A sample dashboard for the MA strategy (with very poorly chosen parameters) looks like this:

.. raw:: html

   <iframe src="_static/dashboard.pdf"
           width="100%"
           height="500px"
           style="border: none;">
   </iframe>

   A registry for adding/using custom metrics and plots will be added in a future version.