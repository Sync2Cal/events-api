from fastapi import HTTPException, APIRouter
from base import CalendarBase, Event, IntegrationBase
import requests
import os
import traceback
from datetime import datetime
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class TwitchCalendar(CalendarBase):
    @property
    def CLIENT_ID(self):
        client_id = os.getenv("TWITCH_CLIENT_ID")
        if not client_id:
            raise ValueError(
                "TWITCH_CLIENT_ID environment variable must be set. "
                "For development, add it to your .env file. "
                "For production, set it as an environment variable."
            )
        return client_id

    @property
    def CLIENT_SECRET(self):
        client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        if not client_secret:
            raise ValueError(
                "TWITCH_CLIENT_SECRET environment variable must be set. "
                "For development, add it to your .env file. "
                "For production, set it as an environment variable."
            )
        return client_secret

    def fetch_events(self, streamer_name: str) -> List[Event]:
        """
        Fetch stream schedule events for a given Twitch streamer.

        Args:
            streamer_name: The Twitch username/streamer name

        Returns:
            List of Event objects representing scheduled streams
        """
        try:
            schedule_data = self._get_stream_schedule(streamer_name)
            events = []

            if schedule_data.get("data") and schedule_data["data"].get("segments"):
                for segment in schedule_data["data"]["segments"]:
                    start_time = datetime.fromisoformat(
                        segment["start_time"].replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(
                        segment["end_time"].replace("Z", "+00:00"))

                    event = Event(
                        uid=f"twitch-{streamer_name}-{segment['id']}",
                        title=segment["title"],
                        start=start_time,
                        end=end_time,
                        description=f"Twitch Stream by {streamer_name}",
                        location=f"https://twitch.tv/{streamer_name}"
                    )
                    events.append(event)
            self.events = events
            return events

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching events: {str(e)}") from e

    def _get_app_access_token(self) -> Optional[str]:
        """Get Twitch app access token for API authentication."""
        url = "https://id.twitch.tv/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "grant_type": "client_credentials"
        }

        try:
            response = requests.post(
                url, data=data, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()['access_token']
            return None
        except requests.RequestException:
            return None

    def _get_stream_schedule(self, username: str) -> dict:
        """Fetch stream schedule data from Twitch API."""
        access_token = self._get_app_access_token()
        if not access_token:
            raise HTTPException(
                status_code=500, detail="Failed to authenticate with Twitch API")

        headers = {
            "Client-ID": self.CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }

        # Get user ID
        user_response = requests.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params={"login": username},
            timeout=10
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=404, detail=f"User {username} not found")

        user_data = user_response.json()
        if not user_data.get("data"):
            raise HTTPException(
                status_code=404, detail=f"User {username} not found")

        user_id = user_data["data"][0]["id"]

        # Get schedule
        schedule_response = requests.get(
            "https://api.twitch.tv/helix/schedule",
            headers=headers,
            params={"broadcaster_id": user_id},
            timeout=10
        )

        if schedule_response.status_code == 404:
            return {"data": {"segments": []}}
        elif schedule_response.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to fetch schedule")

        try:
            schedule_data = schedule_response.json()
            # Ensure the response has the expected structure
            if schedule_data is None:
                return {"data": {"segments": []}}
            if not isinstance(schedule_data, dict):
                return {"data": {"segments": []}}
            if "data" not in schedule_data:
                schedule_data = {"data": schedule_data}
            if schedule_data.get("data") is None:
                schedule_data["data"] = {"segments": []}
            if "segments" not in schedule_data.get("data", {}):
                schedule_data["data"]["segments"] = []
            return schedule_data
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=500, detail=f"Invalid JSON response from Twitch API: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error parsing schedule response: {str(e)}")


class TwitchIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        """
        TODO: Implement function to fetch relevant twitch calendars
        """
        pass
