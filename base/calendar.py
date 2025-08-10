from typing import List
from .models import Event


class CalendarBase:
    def __init__(self, name: str, id: str, icon: str, events: List[Event]):
        self.name = name
        self.icon = icon
        self.id = id
        self.events = events

    def fetch_events(self, *args, **kwargs) -> List[Event]:
        """
        Override this in subclasses.
        Example: fetch_events(start_date, end_date) or fetch_events(auth_token=...)
        """
        raise NotImplementedError(
            f"fetch_events not implemented for {self.name}"
        )


