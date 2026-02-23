"""This module provides a registry for EventRule subclasses.

New custom subclasses ``Subclass`` are added to the registry by appending ``add_event_rule('path.to.module', Subclass)`` to the module.
"""

from tradekit.exec_rules.event_rules.base import EventRule

_CALENDARS = {}

def add_event_rule(name: str, cls: EventRule) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : DatetimeRule
        The custom class (subclass of :class:`~tradekit.exec_rules.event_rules.base.EventRule`)
    """
    if name in _CALENDARS:
        print(f'Calendar {name} already exists')
        return
    
    _CALENDARS[name] = cls

def get_event_rule(name: str) -> EventRule:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it. 

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    EventRule
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found
    """
    if name not in _CALENDARS:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _CALENDARS[name]
    
def make_event_rule(cfg: dict) -> EventRule:
    """This function instatiates a custom subclass of EventRule.

    Parameters
    ----------
    cfg : dict
        The cfg dictionary required to instatiate the custom class

    Returns
    -------
    EventRule
        The instance of the custom class with attributes as per the cfg dictionary
    """
    cls = get_event_rule(cfg['name'])

    kwargs = {k: v for k, v in cfg.items() if k != 'name'}

    return cls(**kwargs)