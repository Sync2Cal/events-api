from fastapi import FastAPI, APIRouter
from integrations.twitch import TwitchIntegration, TwitchCalendar
from integrations.google_sheets import GoogleSheetsIntegration, GoogleSheetsCalendar
from integrations.investing import InvestingIntegration, InvestingCalendar
from integrations.imdb import ImdbIntegration, ImdbCalendar
from integrations.moviedb import MovieDbIntegration, MovieDbCalendar
from integrations.thetvdb import TheTvDbIntegration, TheTvDbCalendar
from integrations.wwe import WweIntegration, WweCalendar
from integrations.shows import ShowsIntegration, ShowsCalendar
from integrations.releases import ReleasesIntegration, ReleasesCalendar
from integrations.sportsdb import SportsDbIntegration, SportsDbCalendar
from base import mount_integration_routes

app = FastAPI(title="Scraper")

# Twitch
twitch_router = APIRouter(tags=["Twitch"], prefix="/twitch")
twitch_integration = TwitchIntegration(
    id="twitch",
    name="Twitch",
    description="Twitch integration",
    base_url="https://api.twitch.tv/helix",
    calendar_class=TwitchCalendar,
    multi_calendar=True
)


mount_integration_routes(twitch_router, twitch_integration)


app.include_router(twitch_router)

# Google Sheets
google_sheets_router = APIRouter(
    prefix="/google-sheets", tags=["Google Sheets"])
google_sheets_integration = GoogleSheetsIntegration(
    id="google_sheets",
    name="Google Sheets",
    description="Google Sheets integration",
    base_url="https://sheets.googleapis.com",
    calendar_class=GoogleSheetsCalendar,
    multi_calendar=False,
)

mount_integration_routes(google_sheets_router, google_sheets_integration)

app.include_router(google_sheets_router)


# Investing
investing_router = APIRouter(prefix="/investing", tags=["Investing"])
investing_integration = InvestingIntegration(
    id="investing",
    name="Investing",
    description="Investing.com integration (earnings, IPO)",
    base_url="https://www.investing.com",
    calendar_class=InvestingCalendar,
    multi_calendar=False,
)

mount_integration_routes(investing_router, investing_integration)

app.include_router(investing_router)


# IMDb
imdb_router = APIRouter(prefix="/imdb", tags=["IMDb"])
imdb_integration = ImdbIntegration(
    id="imdb",
    name="IMDb",
    description="IMDb releases integration",
    base_url="https://www.imdb.com",
    calendar_class=ImdbCalendar,
    multi_calendar=False,
)

mount_integration_routes(imdb_router, imdb_integration)

app.include_router(imdb_router)


# MovieDB
moviedb_router = APIRouter(prefix="/moviedb", tags=["MovieDB"])
moviedb_integration = MovieDbIntegration(
    id="moviedb",
    name="MovieDB",
    description="TheMovieDB upcoming movies",
    base_url="https://www.themoviedb.org",
    calendar_class=MovieDbCalendar,
    multi_calendar=False,
)
mount_integration_routes(moviedb_router, moviedb_integration)
app.include_router(moviedb_router)


# TheTVDB
thetvdb_router = APIRouter(prefix="/thetvdb", tags=["TheTVDB"])
thetvdb_integration = TheTvDbIntegration(
    id="thetvdb",
    name="TheTVDB",
    description="TheTVDB series episodes",
    base_url="https://api4.thetvdb.com",
    calendar_class=TheTvDbCalendar,
    multi_calendar=False,
)
mount_integration_routes(thetvdb_router, thetvdb_integration)
app.include_router(thetvdb_router)


# WWE
wwe_router = APIRouter(prefix="/wwe", tags=["WWE"])
wwe_integration = WweIntegration(
    id="wwe",
    name="WWE",
    description="WWE events",
    base_url="https://www.wwe.com",
    calendar_class=WweCalendar,
    multi_calendar=False,
)
mount_integration_routes(wwe_router, wwe_integration)
app.include_router(wwe_router)


# Shows (TVInsider)
shows_router = APIRouter(prefix="/shows", tags=["Shows"])
shows_integration = ShowsIntegration(
    id="shows",
    name="TV Shows",
    description="TVInsider shows calendar",
    base_url="https://www.tvinsider.com",
    calendar_class=ShowsCalendar,
    multi_calendar=False,
)
mount_integration_routes(shows_router, shows_integration)
app.include_router(shows_router)


# Releases.com
releases_router = APIRouter(prefix="/releases", tags=["Releases"])
releases_integration = ReleasesIntegration(
    id="releases",
    name="Releases",
    description="Releases.com calendars",
    base_url="https://www.releases.com",
    calendar_class=ReleasesCalendar,
    multi_calendar=False,
)
mount_integration_routes(releases_router, releases_integration)
app.include_router(releases_router)


# TheSportsDB
sportsdb_router = APIRouter(prefix="/sportsdb", tags=["SportsDB"])
sportsdb_integration = SportsDbIntegration(
    id="sportsdb",
    name="SportsDB",
    description="TheSportsDB events",
    base_url="https://www.thesportsdb.com",
    calendar_class=SportsDbCalendar,
    multi_calendar=False,
)
mount_integration_routes(sportsdb_router, sportsdb_integration)
app.include_router(sportsdb_router)
