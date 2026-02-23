"""The module providing the Event class.

This is a helper class for storing/accessing infos about a trading event. It is used in combination with notifiers.
"""

from dataclasses import dataclass
from pandas import Timestamp
from typing import Literal, Any

event_type = Literal[
    'trade_exit',
    'engine_finished',
    'engine_crashed',
    'engine_restarted',
    'engine_failed',
    'all_engines_finished'
]

@dataclass
class Event:
    """The helper class providing event info.

    Parameters
    ----------
    type: event_type
        The type of event; this must be one of the following:
        
        - trade_exit
        - engine_finished
        - engine_crashed
        - engine_restarted
        - engine_failed
        - all_engines_finished
    """    
    type: event_type
    source: str
    ts: Timestamp
    payload: dict[str, Any]
    path_to_file: str | None
