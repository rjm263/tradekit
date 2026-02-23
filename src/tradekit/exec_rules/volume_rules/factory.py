"""This module provides a registry for VolumeRule subclasses.

New custom subclasses ``Subclass`` are added to the registry by appending ``add_volume_rule('path.to.module', Subclass)`` to the module.
"""

from tradekit.exec_rules.volume_rules.base import VolumeRule
import inspect

_VOLUME_RULES = {}

def add_volume_rule(name: str, cls: VolumeRule) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : DatetimeRule
        The custom class (subclass of :class:`~tradekit.exec_rules.volume_rules.base.VolumeRule`)
    """
    if name in _VOLUME_RULES:
        print(f'Volume rule {name} already exists')
        return
    
    _VOLUME_RULES[name] = cls

def get_volume_rule(name: str) -> VolumeRule:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it. 

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    VolumeRule
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found
    """
    if name not in _VOLUME_RULES:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _VOLUME_RULES[name]

def load_volume_rule(cfg: dict) -> VolumeRule:
    """This function instantiates the VolumeRule class.

    Here, the dictionary contains *all* attributes of the class, not just init parameters. This function is used when recovering an object whose state was previously saved as a dictionary.

    Parameters
    ----------
    cfg : dict
        The dictionary containing all attributes of the object

    Returns
    -------
    VolumeRule
        The class object resulting from instatiating VolumeRule with the given set of attributes
    """           
    cls = get_volume_rule(cfg['name'])
    
    obj = cls.__new__(cls)
    obj.__dict__.update(
        {k: v for k, v in cfg.items() if k != 'name'}
    )

    return obj
 
def make_volume_rule(cfg: dict) -> VolumeRule:
    """This function instatiates the VolumeRule class.

    This function is used when creating a VolumeRule object fresh, i.e. the dictionary only contains init parameters. The remaining attributes are set *after* initialisation.

    Parameters
    ----------
    cfg : dict
        The dictionary containing init parameters for the class

    Returns
    -------
    VolumeRule
        The class object resulting from instatiating VolumeRule with the given set of init parameters
    """      
    cls = get_volume_rule(cfg['name'])

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