from typing import List, Optional
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase


TMDB_URL = "https://www.themoviedb.org/discover/movie/items"
HEADERS = {
    "accept": "text/html, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.themoviedb.org",
    "referer": "https://www.themoviedb.org/movie/upcoming",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
}


class MovieDbCalendar(CalendarBase):
    def fetch_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_pages: int = 50,
    ) -> List[Event]:
        """
        Fetch upcoming theatrical movie releases from TheMovieDB public website.

        Parameters:
        - start_date (YYYY-MM-DD): Defaults to today if not provided
        - end_date (YYYY-MM-DD): Defaults to start_date + 365 days if not provided
        - max_pages (int): Safety cap for pagination
        """
        try:
            today = datetime.utcnow().date()
            start_dt = (
                datetime.strptime(start_date, "%Y-%m-%d").date()
                if start_date
                else today
            )
            end_dt = (
                datetime.strptime(end_date, "%Y-%m-%d").date()
                if end_date
                else start_dt + timedelta(days=365)
            )

            page_number = 1
            events: List[Event] = []

            while page_number <= max_pages:
                data = {
                    "primary_release_date.gte": start_dt.strftime("%Y-%m-%d"),
                    "primary_release_date.lte": end_dt.strftime("%Y-%m-%d"),
                    "sort_by": "primary_release_date.desc",
                    "with_release_type": "3",
                    "page": str(page_number),
                }

                response = requests.post(TMDB_URL, headers=HEADERS, data=data, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                found_any = False

                for card in soup.find_all("div", class_="card style_1"):
                    title_tag = card.find("h2")
                    date_tag = title_tag.find_next("p") if title_tag else None
                    if not title_tag or not date_tag:
                        continue

                    found_any = True
                    title = title_tag.get_text(strip=True)

                    date_text = date_tag.get_text(strip=True)
                    try:
                        release_dt = datetime.strptime(date_text, "%d %b %Y")
                    except Exception:
                        try:
                            release_dt = datetime.strptime(date_text, "%b %d, %Y")
                        except Exception:
                            continue

                    start = release_dt
                    end = start + timedelta(days=1)

                    uid = f"tmdb-{title.replace(' ', '').lower()}-{start.strftime('%Y%m%d')}"
                    events.append(
                        Event(
                            uid=uid,
                            title=title,
                            start=start,
                            end=end,
                            all_day=True,
                            description="TMDB upcoming movie release",
                            location="https://www.themoviedb.org/movie/upcoming",
                        )
                    )

                if not found_any:
                    break
                page_number += 1

            self.events = events
            return events
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"TMDB request failed: {str(e)}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class MovieDbIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None


