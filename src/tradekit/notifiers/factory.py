"""This module provides a registry containing all Notifier classes.
"""

from tradekit.notifiers.base import Notifier
from tradekit.notifiers.email import EmailNotifier
import inspect

_NOTIFIERS = {
    'email': EmailNotifier
}

def get_notifier(name: str) -> Notifier:
    """This function retrieves a Notifier class from the registry.

    Parameters
    ----------
    name : str
        The name of the Notifier class

    Returns
    -------
    Notifier
        The Notifier class from the registry

    Raises
    ------
    ValueError
        if the registry doesn't contain a Notifier class of the corresponding name
    """    
    try:
        return _NOTIFIERS[name]
    except KeyError:
        raise ValueError(f'Notifier {name} unknown')
    
def make_notifier(cfg: dict) -> Notifier:
    """This function instantiates a Notifier object from a dictionary.

    It is used to create an object from a configuration dictionary.

    Parameters
    ----------
    cfg : dict
        The configuration dictionary containing all init parameters for the Notifier object

    Returns
    -------
    Notifier
        The resulting Notifier object
    """    
    cls = get_notifier(cfg['name'])

    kwargs = {k: v for k, v in cfg.items() if k != 'name'}

    return cls(**kwargs)

