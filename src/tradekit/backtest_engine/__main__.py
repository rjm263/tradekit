"""This module makes BacktestEngine executable.

It makes the engine executable as a python module from a terminal via the command ``python -m tradekit.backtest_engine`` from inside the project folder.
"""

import json
import inspect
import sys
from tradekit.strategies.factory import make_strategy
from tradekit.backtest_engine.engine import BacktestEngine
from tradekit.notifiers.factory import make_notifier


def load_config(path: str) -> dict:  
    """Loads a dictionary of cfg settings from a json file

    Parameters
    ----------
    path : str
        The path to the json cfg file

    Returns
    -------
    dict
        The dictionary containing cfg settings

    Raises
    ------
    RuntimeError
        Configuration file not found
    """
    try:
        with open(path, 'r') as f:
            cfg = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Config file not found: {path}")

    return cfg

def main() -> None:
    """Defines the main function to execute when python -m tradekit.backtest_engine 
    is called
    """
    if len(sys.argv) != 2:
        print('Usage: python -m tradekit.backtest_engine <config.json>')
        sys.exit(1)

    run(sys.argv[1])

def run(cfg_path: str) -> None:
    """This is the main function of this module. It loads a json cfg file and runs a corresponding BacktestEngine. 

    Parameters
    ----------
    cfg_path : str
        The path to the engine cfg file

    Raises
    ------
    ModuleNotFoundError
        Module not found
    """
    cfg = load_config(cfg_path)
   
    engine = BacktestEngine(
        name=cfg['name'], 
        strategy=make_strategy(cfg['strategy'])
    )

    run_args = list(inspect.signature(BacktestEngine.run).parameters.keys())
    kwargs = {k: v for k, v in cfg.items() if k != 'strategy' and k in run_args}

    engine.run(**kwargs)

if __name__ == '__main__':
    main()