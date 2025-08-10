from typing import List
from datetime import datetime, timedelta

from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase

# Inlined helpers from routers.imdb (removed cross-import)
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def parse_imdb_date(date_str: str) -> datetime:
    """
    Parses IMDb-style date like 'Jun 27, 2025' to a datetime object.
    Defaults time to 8AM UTC (for theatrical releases).
    """
    try:
        dt = datetime.strptime(date_str, "%b %d, %Y")
        return dt.replace(hour=8, minute=0)
    except Exception:
        raise ValueError(f"Invalid date format: {date_str}")


def scrape_imdb_movies(country: str = "US") -> List[dict]:
    url = f"https://www.imdb.com/calendar/?region={country}&type=MOVIE"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    results: List[dict] = []

    for article in soup.find_all("article"):
        h3_tag = article.find("h3")
        if not h3_tag:
            continue
        release_date = h3_tag.text.strip()

        for item in article.find_all("li"):
            title_tag = item.find("a", class_="ipc-metadata-list-summary-item__t")
            if not title_tag or not title_tag.text.strip():
                continue

            title = title_tag.text.strip()
            href = title_tag.get("href", "")
            movie_id = None
            location = None

            if href.startswith("/title/tt"):
                parts = href.split("/")
                for part in parts:
                    if part.startswith("tt"):
                        movie_id = part
                        break
                if movie_id:
                    location = f"https://www.imdb.com/title/{movie_id}/"

            genres: List[str] = []
            genre_section = item.find(
                "ul",
                class_=(
                    "ipc-inline-list ipc-inline-list--show-dividers ipc-inline-list--no-wrap "
                    "ipc-inline-list--inline ipc-metadata-list-summary-item__tl base"
                ),
            )
            if genre_section:
                for span in genre_section.find_all("span"):
                    text = span.text.strip()
                    if text:
                        genres.append(text)

            cast: List[str] = []
            cast_section = item.find(
                "ul",
                class_=(
                    "ipc-inline-list ipc-inline-list--show-dividers ipc-inline-list--no-wrap "
                    "ipc-inline-list--inline ipc-metadata-list-summary-item__stl base"
                ),
            )
            if cast_section:
                for span in cast_section.find_all("span"):
                    text = span.text.strip()
                    if text:
                        cast.append(text)

            results.append(
                {
                    "title": title,
                    "release_date": release_date,
                    "genres": genres,
                    "cast": cast,
                    "location": location,
                    "movie_id": movie_id or title.replace(" ", "-").lower(),
                }
            )

    return results


def filter_movies(movies: List[dict], genre: str = "all", actor: str = "all") -> List[dict]:
    genre = genre.lower()
    actor = actor.lower()
    result: List[dict] = []

    for movie in movies:
        genres = [g.lower() for g in movie.get("genres", [])]
        cast = [c.lower() for c in movie.get("cast", [])]

        if (genre == "all" or genre in genres) and (actor == "all" or actor in cast):
            result.append(movie)

    return result


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


