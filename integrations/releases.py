from typing import List
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase


BASE_URL = "https://www.releases.com/partial/Releases.Www.PL.Calendar.Group"


class ReleasesCalendar(CalendarBase):
    def fetch_events(self, kind: str = "games", days_ahead: int = 1, platform: str = "xbox") -> List[Event]:
        """
        Fetch release calendar from releases.com.

        - kind: 'games' | 'tv-series'
        - days_ahead: number of days ahead to fetch
        - platform: platform filter for games (xbox|playstation|pc|android|ios)
        """
        try:
            today = datetime.now()
            events: List[Event] = []

            for i in range(days_ahead):
                date = today + timedelta(days=i)
                formatted_date = f"Y{date.year}-M{date.month}-D{date.day}"
                url = f"{BASE_URL}?Code={formatted_date}&Category={kind}"

                response = requests.post(url, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                cards = soup.find_all("div", class_='RWPCC-CalendarItems-CardControl')
                for card in cards:
                    title_tag = card.find('a', class_='RWPCC-CalendarItems-CardControl-Name')
                    if not title_tag:
                        continue
                    title = title_tag.text

                    if kind == "games":
                        platforms: List[str] = []
                        version_spans = card.find_all('span', class_='RWPCC-CalendarItems-TypeAndVersionsControl-Version')
                        for span in version_spans:
                            if span.get('style') != 'display:none;':
                                platform_text = span.get_text(strip=True).replace('/', '').strip()
                                if platform_text and not platform_text.startswith('+'):
                                    platforms.append(platform_text)
                        track_buttons = card.find_all('button', class_='RWPCC-Trackbutton-TrackbuttonControl-version')
                        for button in track_buttons:
                            name = button.find('span', class_='RWPCC-Trackbutton-TrackbuttonControl-versionName').text
                            if name not in platforms:
                                platforms.append(name)

                        if not any(platform.lower() in p.lower() for p in platforms):
                            continue

                    begin = datetime(date.year, date.month, date.day)
                    events.append(
                        Event(
                            uid=f"releases-{kind}-{title.replace(' ', '').lower()}-{begin.strftime('%Y%m%d')}",
                            title=title,
                            start=begin,
                            end=begin + timedelta(days=1),
                            all_day=True,
                            description=f"Releases.com {kind}",
                            location="https://www.releases.com",
                        )
                    )

            self.events = events
            return events
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class ReleasesIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None


