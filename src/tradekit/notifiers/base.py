"""This module provides the Notifier base class.

It is used as the parent class for all notifiers.
"""

from tradekit.notifiers.events import Event

class Notifier:
    """The base class for notifiers.
    """    
    def notify(self, event: Event) -> None:
        """Sends a notification about a trading event.

        Parameters
        ----------
        event : Event
            The event to be notified about, see :class:`~tradekit.notifiers.events.Event`

        Raises
        ------
        NotImplementedError
            if the method is not implemented
        """        
        raise NotImplementedError