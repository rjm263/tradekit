Tradekit
========

This package provides a leightweight, modular toolkit for live testing and evaluating algorithmic trading strategies.
It supports running multiple trade engines on a server and can notify the user about engine progress. By default, after an engine finished running, it creates a dashboard of relevant performance metrics.

The repository is available on [Github](https://github.com/rjm263/tradekit). 
The package is available on [PyPI](https://test.pypi.org/project/tradekit/) and can be installed via 

``pip install tradekit``

For the documentation pages see [here](https://rjm263.github.io/tradekit/).

Overview
--------

The package provides a framework for live trading and backtesting in a modular way. The idea is for the user to code their own algo-trading strategies, take-profit and stop-loss rules, as well as other trading rules involving date/time, macro event and volume restrictions. Afterwards, the user can add them into the corresponding package registry and use them for testing.

So far, all market data is obtained from [Yahoo!® Finance](https://finance.yahoo.com/) via the [yfinance](https://pypi.org/project/yfinance/) package.


Feature Wishlist
----------------

There are plenty of features that will (hopefully) be added in future versions. The main ones are:

- support for additional market data APIs (TradingView, Bloomberg etc.)
- a common, customisable data loader for technicals and fundamentals
- a registry for custom metrics and visualisation
- additional notifiers (text message, signal, slack)
- ML features for market data analysis and strategy selection 
