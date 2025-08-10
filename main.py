from fastapi import FastAPI, APIRouter
from integrations.twitch import TwitchIntegration, TwitchCalendar
from integrations.google_sheets import (
    GoogleSheetsIntegration,
    GoogleSheetsCalendar,
)
from integrations.investing import InvestingIntegration, InvestingCalendar
from integrations.imdb import ImdbIntegration, ImdbCalendar
from integrations.moviedb import MovieDbIntegration, MovieDbCalendar
from integrations.thetvdb import TheTvDbIntegration, TheTvDbCalendar
from integrations.wwe import WweIntegration, WweCalendar
from integrations.shows import ShowsIntegration, ShowsCalendar
from integrations.releases import ReleasesIntegration, ReleasesCalendar
from integrations.sportsdb import SportsDbIntegration, SportsDbCalendar
from base import mount_integration_routes


app = FastAPI(title="Events API")


integrations = [
    TwitchIntegration(
        id="twitch",
        name="Twitch",
        description="Twitch integration",
        base_url="https://api.twitch.tv/helix",
        calendar_class=TwitchCalendar,
        multi_calendar=True,
    ),
    GoogleSheetsIntegration(
        id="google_sheets",
        name="Google Sheets",
        description="Google Sheets integration",
        base_url="https://sheets.googleapis.com",
        calendar_class=GoogleSheetsCalendar,
        multi_calendar=False,
    ),
    InvestingIntegration(
        id="investing",
        name="Investing",
        description="Investing.com integration (earnings, IPO)",
        base_url="https://www.investing.com",
        calendar_class=InvestingCalendar,
        multi_calendar=False,
    ),
    ImdbIntegration(
        id="imdb",
        name="IMDb",
        description="IMDb releases integration",
        base_url="https://www.imdb.com",
        calendar_class=ImdbCalendar,
        multi_calendar=False,
    ),
    MovieDbIntegration(
        id="moviedb",
        name="MovieDB",
        description="TheMovieDB upcoming movies",
        base_url="https://www.themoviedb.org",
        calendar_class=MovieDbCalendar,
        multi_calendar=False,
    ),
    TheTvDbIntegration(
        id="thetvdb",
        name="TheTVDB",
        description="TheTVDB series episodes",
        base_url="https://api4.thetvdb.com",
        calendar_class=TheTvDbCalendar,
        multi_calendar=False,
    ),
    WweIntegration(
        id="wwe",
        name="WWE",
        description="WWE events",
        base_url="https://www.wwe.com",
        calendar_class=WweCalendar,
        multi_calendar=False,
    ),
    ShowsIntegration(
        id="shows",
        name="TV Shows",
        description="TVInsider shows calendar",
        base_url="https://www.tvinsider.com",
        calendar_class=ShowsCalendar,
        multi_calendar=False,
    ),
    ReleasesIntegration(
        id="releases",
        name="Releases",
        description="Releases.com calendars",
        base_url="https://www.releases.com",
        calendar_class=ReleasesCalendar,
        multi_calendar=False,
    ),
    SportsDbIntegration(
        id="sportsdb",
        name="SportsDB",
        description="TheSportsDB events",
        base_url="https://www.thesportsdb.com",
        calendar_class=SportsDbCalendar,
        multi_calendar=False,
    ),
]


for integration in integrations:
    prefix = f"/{integration.id.replace('_', '-')}"
    router = APIRouter(prefix=prefix, tags=[integration.name])
    mount_integration_routes(router, integration)
    app.include_router(router)
