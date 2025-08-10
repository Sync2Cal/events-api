from typing import List
from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase


def _convert_date(date_str: str) -> str | None:
    try:
        parsed_date = datetime.strptime(date_str, "%A, %B %d")
        parsed_date = parsed_date.replace(year=datetime.now().year)
        return parsed_date.strftime("%Y%m%d")
    except ValueError:
        return None


def _create_slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    text = re.sub(r'^[_\s]+|[_\s]+$', '', text)
    text = text.replace('&', 'and').replace('+', '')
    return text


def _scrape_shows() -> List[list]:
    url = "https://www.tvinsider.com/shows/calendar/"
    response = requests.get(url, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")

    shows_data: List[list] = []
    dates = soup.find_all("h6")
    for date in dates:
        formatted_date = _convert_date(date.text.strip())
        next_sibling = date.find_next_sibling()

        while next_sibling and next_sibling.name == "a":
            network_img = next_sibling.find("img", class_="network-logo")
            show_name_tag = next_sibling.find("h3")
            show_type_tag = next_sibling.find("h5")
            images = next_sibling.find_all("img")
            poster_img = images[-1] if images else None
            show_url = next_sibling["href"] if next_sibling.has_attr("href") else ""

            if network_img and show_name_tag:
                platform = network_img.get("alt", "")
                network_img_url = network_img.get("src", "")
                show_name = show_name_tag.text.strip()
                show_poster_url = poster_img.get("src", "") if poster_img else ""
                genre = show_type_tag.text.strip() if show_type_tag else ""

                if "Streaming Premiere" in genre or "Movie Premiere" in genre:
                    next_sibling = next_sibling.find_next_sibling()
                    continue

                if "Season" in genre and "Premiere" in genre:
                    show_name = f"{show_name} ({genre})"
                    genre = "Season Premiere"

                shows_data.append(
                    [show_name, platform, formatted_date, network_img_url, show_poster_url, genre, show_url]
                )

            next_sibling = next_sibling.find_next_sibling()

    return shows_data


def _get_tmsid(show_url: str) -> str | None:
    url = f"https://www.tvinsider.com{show_url}"
    response = requests.get(url, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")
    button = soup.select_one(".button-episodes[data-tmsid]")
    if button:
        return button.get("data-tmsid")
    match = re.search(r"'tmsid':'(.*?)'", response.text)
    return match.group(1) if match else None


def _scrape_episodes(show_url: str) -> List[dict]:
    tmsid = _get_tmsid(show_url)
    if not tmsid:
        return []

    url = (
        "https://www.tvinsider.com/wp-admin/admin-ajax.php?action=fetch_show_episodes"
        f"&tmsid={tmsid}"
    )
    headers = {
        "accept": "*/*",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
    }
    response = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")

    current_date = datetime.now()
    episodes: List[dict] = []
    for episode in soup.find_all("div", class_="show-episode"):
        date_str = episode.find("time").text.strip()
        try:
            episode_date = datetime.strptime(date_str, "%b %d, %Y")
        except ValueError:
            continue
        if episode_date > current_date:
            title = episode.find("h3").text
            season_episode = episode.find("h4").text
            episodes.append({
                "title": title,
                "season_episode": season_episode,
                "date": episode_date.strftime("%Y%m%d")
            })
    return episodes


class ShowsCalendar(CalendarBase):
    def fetch_events(self, mode: str, slug: str) -> List[Event]:
        """
        Fetch TV shows calendar from TVInsider.

        - mode: 'platform' | 'genre' | 'show'
        - slug: corresponding slug for the mode
        """
        try:
            shows_data = _scrape_shows()
            events: List[Event] = []

            if mode == "platform":
                platform_name = None
                for show in shows_data:
                    if _create_slug(show[1]) == slug:
                        platform_name = show[1]
                        break
                if not platform_name:
                    raise HTTPException(status_code=404, detail="Platform not found")
                for show in shows_data:
                    if _create_slug(show[1]) != slug:
                        continue
                    show_name, platform, date, *_rest = show
                    events.append(
                        Event(
                            uid=f"show-platform-{_create_slug(show_name)}-{date}",
                            title=show_name,
                            start=datetime.strptime(date, "%Y%m%d"),
                            end=datetime.strptime(date, "%Y%m%d"),
                            all_day=True,
                            description=f"Platform: {platform}",
                            location="",
                        )
                    )

            elif mode == "genre":
                genre_name = None
                for show in shows_data:
                    if _create_slug(show[5]) == slug:
                        genre_name = show[5]
                        break
                if not genre_name:
                    raise HTTPException(status_code=404, detail="Genre not found")
                for show in shows_data:
                    if _create_slug(show[5]) != slug:
                        continue
                    show_name, platform, date, *_rest = show
                    events.append(
                        Event(
                            uid=f"show-genre-{_create_slug(show_name)}-{date}",
                            title=show_name,
                            start=datetime.strptime(date, "%Y%m%d"),
                            end=datetime.strptime(date, "%Y%m%d"),
                            all_day=True,
                            description=f"Platform: {platform}\nGenre: {genre_name}",
                            location="",
                        )
                    )

            elif mode == "show":
                matching_show = None
                for show in shows_data:
                    if _create_slug(show[0]) == slug:
                        matching_show = show
                        break
                if not matching_show:
                    raise HTTPException(status_code=404, detail="Show not found")

                episodes = _scrape_episodes(matching_show[6])
                for ep in episodes:
                    date = ep["date"]
                    begin = datetime.strptime(date, "%Y%m%d")
                    events.append(
                        Event(
                            uid=f"show-ep-{_create_slug(ep['season_episode'])}-{date}",
                            title=f"{ep['season_episode']} - {ep['title']}",
                            start=begin,
                            end=begin,
                            all_day=True,
                            description=f"Show: {matching_show[0]}\nPlatform: {matching_show[1]}",
                            location="",
                        )
                    )
            else:
                raise HTTPException(status_code=400, detail="Invalid mode. Use platform|genre|show")

            self.events = events
            return events
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class ShowsIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None


