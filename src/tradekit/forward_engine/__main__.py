"""This module makes ForwardEngine executable.

It makes the engine executable as a python module from a terminal via the command ``python -m tradekit.forward_engine`` from inside the project folder.
"""

import json
import inspect
import sys
from tradekit.strategies.factory import make_strategy
from tradekit.forward_engine.engine import ForwardEngine
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
    """Defines the main function to execute when python -m tradekit.forward_engine 
    is called.
    """
    if len(sys.argv) != 2:
        print('Usage: python -m tradekit.engine <config.json>')
        sys.exit(1)

    run(sys.argv[1])

def run(cfg_path: str) -> None:
    """This is the main function of this module. It loads a json cfg file and runs a corresponding ForwardEngine. 

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
    
    if 'notifiers' in cfg:
        notifiers = [make_notifier(d) for d in cfg['notifiers']]

    engine = ForwardEngine(
        name=cfg['name'], 
        strategy=make_strategy(cfg['strategy']), 
        notifiers=notifiers
    )

    run_args = list(inspect.signature(ForwardEngine.run).parameters.keys())
    kwargs = {k: v for k, v in cfg.items() if k != 'strategy' and k in run_args}

    engine.run(**kwargs)

if __name__ == '__main__':
    main()