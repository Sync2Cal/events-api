from typing import List
from datetime import datetime
import os

import requests
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase


API_ROOT = "https://www.thesportsdb.com/api/v1/json"


class SportsDbCalendar(CalendarBase):
    def fetch_events(self, mode: str, id: str) -> List[Event]:
        """
        Fetch events from TheSportsDB.

        - mode: 'league' or 'team'
        - id: league id (e.g., 4328) or team id (e.g., 133602)
        """
        try:
            api_key = os.getenv("SPORTSDB_API_KEY")
            if not api_key:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Missing TheSportsDB API key. Set SPORTSDB_API_KEY in the environment."
                    ),
                )

            base = f"{API_ROOT}/{api_key}"
            if mode == "league":
                url = f"{base}/eventsnextleague.php?id={id}"
            elif mode == "team":
                url = f"{base}/eventsnext.php?id={id}"
            else:
                raise HTTPException(status_code=400, detail="Invalid mode. Use 'league' or 'team'.")

            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            items = data.get("events", []) or []

            events: List[Event] = []
            for item in items:
                try:
                    title = item.get("strEvent")
                    start = datetime.fromisoformat(item.get("strTimestamp"))
                    uid = item.get("idEvent")
                    events.append(
                        Event(
                            uid=uid,
                            title=title,
                            start=start,
                            end=start,
                            all_day=False,
                            description="",
                            location="",
                        )
                    )
                except Exception:
                    continue

            self.events = events
            return events
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class SportsDbIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None


