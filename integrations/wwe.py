from typing import List
from datetime import datetime, timedelta

import requests
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase


API_URL = "https://www.wwe.com/api/events-search-results/all-events/all-dates/0/0/0/0"


def parse_wwe_datetime(date_str: str, time_str: str) -> datetime:
    date_parts = date_str.split(", ")
    if len(date_parts) != 2:
        raise ValueError(f"Invalid date format: {date_str}")
    month_day = date_parts[1]

    time_parts = time_str.split(" ")
    if len(time_parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}")
    time_value = time_parts[0]
    ampm = time_parts[1]

    hour_minute = time_value.split(":")
    if len(hour_minute) != 2:
        raise ValueError(f"Invalid time format: {time_value}")
    hour = int(hour_minute[0])
    minute = int(hour_minute[1])

    if ampm.upper() == "PM" and hour != 12:
        hour += 12
    elif ampm.upper() == "AM" and hour == 12:
        hour = 0

    current_year = datetime.now().year

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    month_day_parts = month_day.split(" ")
    if len(month_day_parts) != 2:
        raise ValueError(f"Invalid month/day format: {month_day}")
    month_str = month_day_parts[0]
    day = int(month_day_parts[1])
    if month_str not in month_map:
        raise ValueError(f"Invalid month: {month_str}")
    month = month_map[month_str]

    return datetime(current_year, month, day, hour, minute)


class WweCalendar(CalendarBase):
    def fetch_events(self) -> List[Event]:
        try:
            response = requests.get(API_URL, timeout=20)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch WWE events")

            data = response.json()
            events: List[Event] = []
            for item in data:
                if item.get("type") != "event":
                    continue
                try:
                    start_time = parse_wwe_datetime(item["date"], item["time"])
                    end_time = start_time + timedelta(hours=3)
                    # WWE site seems US-based; if you previously offset by +5 hours in routers,
                    # leave as-is or adjust here. We'll not add arbitrary offset here.

                    events.append(
                        Event(
                            uid=f"wwe-{item['nid']}",
                            title=item["title"],
                            start=start_time,
                            end=end_time,
                            all_day=False,
                            description=f"WWE Event: {item.get('teaser_title', item['title'])}",
                            location=item.get('location', f"https://www.wwe.com{item['link']}")
                            if item.get('link') else item.get('location', ""),
                        )
                    )
                except (ValueError, KeyError):
                    continue

            self.events = events
            return events
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class WweIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None


