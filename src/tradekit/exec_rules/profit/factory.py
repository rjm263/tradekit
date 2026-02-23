"""This module provides a registry for custom ProfitRule subclasses.

New custom subclasses ``Subclass`` are added to the registry by appending ``add_profit('path.to.module', Subclass)`` to the module.
"""

from tradekit.exec_rules.profit.base import ProfitRule
import inspect

_FORWARD_PROFIT_RULES = {}

def add_profit(name: str, cls: ProfitRule) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : ProfitRule
        The custom class (subclass of :class:`~tradekit.exec_rules.profit.base.ProfitRule`)
    """
    if name in _FORWARD_PROFIT_RULES:
        print(f'Profit rule {name} already exists')
        return
    
    _FORWARD_PROFIT_RULES[name] = cls

def get_profit(name: str) -> ProfitRule:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it. 

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    ProfitRule
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found
    """
    if name not in _FORWARD_PROFIT_RULES:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _FORWARD_PROFIT_RULES[name]
    
def show_profit_names() -> list[str]:
    """This function prints a list of all classes currently contained in the registry.

    Returns
    -------
    list[str]
        The list of names of classes contained in the registry
    """    
    return list(_FORWARD_PROFIT_RULES.keys())


def load_profit(cfg: dict) -> ProfitRule:
    """This function instantiates the ProfitRule class.

    Here, the dictionary contains *all* attributes of the class, not just init parameters. This function is used when recovering an object whose state was previously saved as a dictionary.

    Parameters
    ----------
    cfg : dict
        The dictionary containing all attributes of the object

    Returns
    -------
    ProfitRule
        The class object resulting from instatiating ProfitRule with the given set of attributes
    """     
    cls = get_profit(cfg['name'])
    
    obj = cls.__new__(cls)
    obj.__dict__.update(
        {k: v for k, v in cfg.items() if k != 'name'}
    )

    return obj

def make_profit(cfg: dict) -> ProfitRule:
    """This function instatiates the ProfitRule class.

    This function is used when creating a ProfitRule object fresh, i.e. the dictionary only contains init parameters. The remaining attributes are set *after* initialisation.

    Parameters
    ----------
    cfg : dict
        The dictionary containing init parameters for the class

    Returns
    -------
    ProfitRule
        The class object resulting from instatiating ProfitRule with the given set of init parameters
    """
    cls = get_profit(cfg['name'])

    sig = inspect.signature(cls.__init__)

    init_keys = {key for key, _ in sig.parameters.items() if key != 'self'}
    
    kwargs = {k: v for k, v in cfg.items() if k != 'name' and k in init_keys}
    other_attr = {k: v for k, v in cfg.items() if k != 'name' and k not in init_keys}

    obj = cls(**kwargs)

    if other_attr:
        for k, v in other_attr.items():
            if hasattr(obj, k):
                setattr(obj, k, v)

    return obj