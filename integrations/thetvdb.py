from typing import List
from datetime import datetime, timedelta
import os

import requests
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase


API_BASE = "https://api4.thetvdb.com/v4"


class TheTvDbCalendar(CalendarBase):
    def fetch_events(self, series_id: int) -> List[Event]:
        """
        Fetch default episode list for a series from TheTVDB and convert to events.

        Input:
        - series_id: integer id from thetvdb URL
        """
        try:
            url = f"{API_BASE}/series/{series_id}/episodes/default?page=0"
            api_key = os.getenv("THE_TVDB_API_KEY")
            bearer_token = os.getenv("THE_TVDB_BEARER_TOKEN")
            if not api_key or not bearer_token:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Missing TheTVDB credentials. Set THE_TVDB_API_KEY and THE_TVDB_BEARER_TOKEN in environment."
                    ),
                )
            headers = {
                "x-api-key": api_key,
                "Authorization": f"Bearer {bearer_token}",
            }

            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "success":
                raise HTTPException(status_code=404, detail="Series not found or API error")

            series_data = data.get("data", {})
            series_info = series_data.get("series", {})
            episodes = series_data.get("episodes", [])
            if not episodes:
                raise HTTPException(status_code=404, detail="No episodes found for this series")

            series_name = series_info.get("name", f"Series {series_id}")
            events: List[Event] = []

            for episode in episodes:
                aired_date = episode.get("aired")
                if not aired_date:
                    continue

                try:
                    date_obj = datetime.strptime(aired_date, "%Y-%m-%d")
                except ValueError:
                    continue

                begin = date_obj
                end = begin + timedelta(days=1)

                episode_name = episode.get("name", "Untitled Episode")
                episode_number = episode.get("number")
                season_number = episode.get("seasonNumber")

                if season_number is not None and episode_number is not None:
                    title = f"{series_name} S{int(season_number):02d}E{int(episode_number):02d}: {episode_name}"
                else:
                    title = f"{series_name}: {episode_name}"

                description = episode.get("overview", "")

                events.append(
                    Event(
                        uid=str(episode.get("id", "")),
                        title=title,
                        start=begin,
                        end=end,
                        all_day=True,
                        description=description,
                        location="",
                    )
                )

            self.events = events
            return events
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"TheTVDB request failed: {str(e)}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class TheTvDbIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None


