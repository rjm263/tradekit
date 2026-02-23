"""This module provides a registry for custom StopRule subclasses.

New custom subclasses ``Subclass`` are added to the registry by appending ``add_stop('path.to.module', Subclass)`` to the module.
"""

from tradekit.exec_rules.stop.base import StopRule
import inspect


_FORWARD_STOP_RULES = {}

def add_stop(name: str, cls: StopRule) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : StopRule
        The custom class (subclass of :class:`~tradekit.exec_rules.stop.base.StopRule`)
    """
    if name in _FORWARD_STOP_RULES:
        print(f'Stop rule {name} already exists')
        return
    
    _FORWARD_STOP_RULES[name] = cls

def get_stop(name: str) -> StopRule:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it. 

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    StopRule
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found
    """
    if name not in _FORWARD_STOP_RULES:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _FORWARD_STOP_RULES[name]
    
def show_stop_names() -> list[StopRule]:
    """Prints a list of all classes currently contained in the registry.

    Returns
    -------
    list[StopRule]
        The list of classes contained in the registry
    """    
    return list(_FORWARD_STOP_RULES.keys())

def load_stop(cfg: dict) -> StopRule:
    """This function instantiates the StopRule class.

    Here, the dictionary contains *all* attributes of the class, not just init parameters. This function is used when recovering an object whose state was previously saved as a dictionary.

    Parameters
    ----------
    cfg : dict
        The dictionary containing all attributes of the object

    Returns
    -------
    StopRule
        The class object resulting from instatiating StopRule with the given set of attributes
    """     
    cls = get_stop(cfg['name'])
    
    obj = cls.__new__(cls)
    obj.__dict__.update(
        {k: v for k, v in cfg.items() if k != 'name'}
    )

    return obj

def make_stop(cfg: dict) -> StopRule:
    """This function instatiates the StopRule class.

    This function is used when creating a StopRule object fresh, i.e. the dictionary only contains init parameters. The remaining attributes are set *after* initialisation.

    Parameters
    ----------
    cfg : dict
        The dictionary containing init parameters for the class

    Returns
    -------
    StopRule
        The class object resulting from instatiating StopRule with the given set of init parameters
    """
    cls = get_stop(cfg['name'])

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