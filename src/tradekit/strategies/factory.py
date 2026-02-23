"""This module provides a registry for custom Strategy subclasses.

It holds strategy classes whose parent class is :class:`~tradekit.strategies.base.Strategy`. New custom classes ``Class`` are added to the registry by appending ``add_strategy(path.to.module, Class).
"""

from tradekit.strategies.base import Strategy
import inspect

_STRATEGIES = {}

def add_strategy(name: str, cls: Strategy) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : Strategy
        The custom class (subclass of :class:`~tradekit.strategies.base.Strategy`)
    """    
    if name in _STRATEGIES:
        print(f'Strategy {name} already exists')
        return
    
    _STRATEGIES[name] = cls

def get_strategy(name: str) -> Strategy:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    Strategy
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found    
    """    
    if name not in _STRATEGIES:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _STRATEGIES[name]
    
def rm_strategy(name: str) -> None:
    """This function removes a strategy from the registry.

    Parameters
    ----------
    name : str
        The path to the module containing the class
    """    
    try:
        del _STRATEGIES[name]
    except KeyError:
        print(f'Strategy {name} not registered')

def show_strategy_names() -> list[str]:
    """This function prints a list of all classes currently contained in the registry.

    Returns
    -------
    list[str]
        The list of names of classes contained in the registry
    """    
    return list(_STRATEGIES.keys())

def load_strategy(cfg: dict) -> Strategy:
    """This function instantiates the Strategy class.

    Here, the dictionary contains *all* attributes of the class, not just init parameters. This function is used when recovering an object whose state was previously saved as a dictionary.

    Parameters
    ----------
    cfg : dict
        The dictionary containing all attributes of the object

    Returns
    -------
    Strategy
        The class object resulting from instatiating Strategy with the given set of attributes
    """  
    cls = get_strategy(cfg['name'])

    obj = cls.__new__(cls)
    obj.__dict__.update(
        {k: v for k, v in cfg.items() if k != 'name'}
    )

    return obj

def make_strategy(cfg: dict) -> Strategy:
    """This function instatiates the Strategy class.

    This function is used when creating a Strategy object fresh, i.e. the dictionary only contains init parameters. The remaining attributes are set *after* initialisation.

    Parameters
    ----------
    cfg : dict
        The dictionary containing init parameters for the class

    Returns
    -------
    Strategy
        The class object resulting from instatiating Strategy with the given set of init parameters
    """
    cls = get_strategy(cfg['name'])

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