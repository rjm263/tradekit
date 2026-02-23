Templates
=========

Here are some sample templates for trading strategies, rules and fee models. In order to use them, the respective python file is added to the project folder and its path added to the engine configuration file (see the example file structure and config file in `User Guide <user_guide.html>`_).  

Strategies
----------

- moving average crossover: `ma_crossover.py <../../../templates/my_strategies/ma_crossover.py>`_

    A simple trading strategy that creates buy signals when the fast moving average (MA) crosses over the slow MA and sell signals when it crosses under the slow MA.

    The take-profit and stop-loss chosen in the template happen at a static price level.

Take-Profit Exits
-----------------

- static price level: `static.py <../../templates/my_profit_rules/static.py>`_

    A simple take-profit exit where the trade is exited if the current price crosses over a static price level with respect to the entry price (e.g. 300bps above entry).

- constant price level: `constant.py <../../templates/my_profit_rules/constant.py>`_

    A simple take-profit exit where the trade is exited if the current price crosses over a constant price level.

Stop-Loss Exits
---------------

- static price level: `static.py <../../templates/my_stop_rules/static.py>`_

    A simple stop-loss exit where the trade is exited if the current price crosses under a static price level with respect to the entry price (e.g. 100bps below entry).

- dynamic price level: `dynamic.py <../../templates/my_stop_rules/dynamic.py>`_

    A stop-loss exit where the price level is adjusted dynamically, i.e. after a custom amount of bars the price level is set to x bps above the maximum price hit during that period.

- variable dynamic price level: `var_dynamic.py <../../templates/my_stop_rules/var_dynamic.py>`_

    A stop-loss exit where the price level is adjusted dynamically and the increment is variable. The price level is determined similar to the dynamic method, but with an extra increment consisting of a custom percentage of the difference between the maximum and starting price of each period.

Volume Rules
------------

- volume interval: `interval.py <../../templates/my_volume_rules/interval.py>`_

    A simple rule restricting the engine to execute trades only if traded volumes are withing a given interval.

Event Rules
-----------

- earnings: `earnings.py <../../templates/my_event_rules/earnings.py>`_

    A simple rule restricting the engine not to trade on days when earnings reports for the involved symbols are expected to be published.

Datetime Rules
--------------

- days: `day.py <../../templates/my_date_rules/day.py>`_

    A simple rule restricting the engine to exclude certain days from trading (e.g. don't trade on Fridays).

- time intervals: `time_interval.py <../../templates/my_date_rules/time_interval.py>`_

    A simple rule restricting the engine to only trade within a given time interval (e.g. only trade between 11am and 3pm).

Fee Models
----------

- broker A: `broker_a.py <../../templates/my_fee_models/broker_a.py>`_

    A fee model for a sample broker, charging an amount of bps of the capital invested plus a fixed base fee.