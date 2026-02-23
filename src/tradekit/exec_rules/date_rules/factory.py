"""This module provides a registry for DatetimeRule subclasses.

New custom subclasses ``Subclass`` are added to the registry by appending ``add_datetime_rule('path.to.module', Subclass)`` to the module.
"""

from tradekit.exec_rules.date_rules.base import DatetimeRule

_DATETIMES = {}

def add_datetime_rule(name: str, cls: DatetimeRule) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : DatetimeRule
        The custom class (subclass of :class:`~tradekit.exec_rules.date_rules.base.DatetimeRule`)
    """
    if name in _DATETIMES:
        print(f'Datetime rule {name} already exists')
        return
    
    _DATETIMES[name] = cls

def get_datetime_rule(name: str) -> DatetimeRule:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it. 

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    DatetimeRule
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found
    """
    if name not in _DATETIMES:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _DATETIMES[name]
    
def make_datetime_rule(cfg: dict) -> DatetimeRule:
    """This function instatiates a custom subclass of DatetimeRule.

    Parameters
    ----------
    cfg : dict
        The cfg dictionary required to instatiate the custom class

    Returns
    -------
    DatetimeRule
        The instance of the custom class with attributes as per the cfg dictionary
    """
    cls = get_datetime_rule(cfg['name'])

    kwargs = {k: v for k, v in cfg.items() if k != 'name'}

    return cls(**kwargs)