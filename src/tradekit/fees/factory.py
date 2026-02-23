"""This module provides a registry for FeeModel subclasses.

New custom subclasses ``Subclass`` are added to the registry by appending ``add_fee_model('path.to.module', Subclass)`` to the module.
"""

from tradekit.fees.base import FeeModel

_FEE_MODELS = {}

def add_fee_model(name: str, cls: FeeModel) -> None:
    """This function adds a custom class to the registry.

    Parameters
    ----------
    name : str
        The path to the custom module containing the class
    cls : FeeModel
        The custom class (subclass of :class:`~tradekit.fees.base.FeeModel`)
    """
    if name in _FEE_MODELS:
        print(f'Fee model {name} already exists')
        return
    
    _FEE_MODELS[name] = cls

def get_fee_model(name: str) -> FeeModel:
    """This function retrieves a custom class from the registry. If it's not registered yet, it adds it. 

    Parameters
    ----------
    name : str
        The path to the custom module containing the class

    Returns
    -------
    FeeModel
        The custom class from the registry

    Raises
    ------
    ModuleNotFoundError
        if the module from which the custom class should be imported can't be found
    """
    if name not in _FEE_MODELS:
        try:
            __import__(name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module {name} not found')
        
    return _FEE_MODELS[name]
    
def make_fee_model(cfg: dict) -> FeeModel:
    """This function instatiates a custom subclass of FeeModel.

    Parameters
    ----------
    cfg : dict
        The cfg dictionary required to instatiate the custom class

    Returns
    -------
    FeeModel
        The instance of the custom class with attributes as per the cfg dictionary
    """
    cls = get_fee_model(cfg['name'])

    kwargs = {k: v for k, v in cfg.items() if k != 'name'}

    return cls(**kwargs)