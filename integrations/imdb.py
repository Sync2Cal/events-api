from typing import List
from datetime import timedelta

from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase

# Reuse scraping utils from router implementation
from routers.imdb import scrape_imdb_movies, parse_imdb_date, filter_movies


class ImdbCalendar(CalendarBase):
    def fetch_events(
        self,
        genre: str = "all",
        actor: str = "all",
        country: str = "US",
    ) -> List[Event]:
        """
        Fetch theatrical movie releases from IMDb as calendar events.

        Parameters:
        - genre (str): Filter by genre (case-insensitive). Use "all" for no filter.
        - actor (str): Filter by actor (case-insensitive). Use "all" for no filter.
        - country (str): IMDb region code, e.g., "US", "IN", "GB".
        """
        try:
            all_movies = scrape_imdb_movies(country=country)
            filtered = filter_movies(all_movies, genre, actor)

            events: List[Event] = []
            for movie in filtered:
                try:
                    date = parse_imdb_date(movie["release_date"])
                    next_day = date + timedelta(days=1)

                    cast_str = ", ".join(movie["cast"]) if movie["cast"] else "Cast not available"
                    genres_str = ", ".join(movie["genres"]) if movie["genres"] else "N/A"
                    imdb_url = movie["location"] or "https://www.imdb.com"

                    description = (
                        f"Title: {movie['title']} | Genres: {genres_str} | Cast: {cast_str} | IMDb: {imdb_url}"
                    )

                    events.append(
                        Event(
                            uid=f"imdb-{movie['movie_id']}",
                            title=movie["title"],
                            start=date,
                            end=next_day,
                            all_day=True,
                            description=description,
                            location=imdb_url,
                        )
                    )
                except ValueError:
                    # Skip problematic entries
                    continue

            self.events = events
            return events
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch IMDb events: {str(e)}") from e


class ImdbIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        """
        Placeholder for future multi-calendar support.
        """
        return None


