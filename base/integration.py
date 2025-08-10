from typing import Type
from .calendar import CalendarBase


class IntegrationBase:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        base_url: str,
        calendar_class: Type[CalendarBase],
        multi_calendar: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.base_url = base_url
        self.multi_calendar = multi_calendar
        self.calendar_class = calendar_class

    def master_csv(self):
        """
        Fetches all calendars and returns a CSV file for bulk upload.
        """
        if not self.multi_calendar:
            raise Exception(
                "This integration does not support multiple calendars"
            )
        # TODO: implement CSV generation logic
        return None

    def fetch_calendars(self, *args, **kwargs):
        """
        Override this in subclasses.
        Example: fetch_calendars(region='US', api_key='xyz')
        """
        raise NotImplementedError(
            f"fetch_calendars not implemented for {self.name}"
        )


