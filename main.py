from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
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
from integrations.weather import DailyWeatherForecastIntegration, DailyWeatherForecastCalendar
from integrations.weather_geocode import geocode_router
from base import mount_integration_routes


app = FastAPI(title="Events API")

# Add CORS middleware to allow frontend requests
# Security: When allow_credentials=True, we cannot use allow_origins=["*"]
# Must specify exact origins to prevent cross-site request attacks
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    # Parse comma-separated list of allowed origins
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Default to production origins if not set
    allowed_origins = [
        "https://sync2cal.com",
        "https://www.sync2cal.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    DailyWeatherForecastIntegration(
        id="daily-weather-forecast",
        name="Daily Weather Forecast",
        description="Daily weather forecasts",
        base_url="https://api.openweathermap.org",
        calendar_class=DailyWeatherForecastCalendar,
        multi_calendar=False,
    ),
]


for integration in integrations:
    prefix = f"/{integration.id.replace('_', '-')}"
    router = APIRouter(prefix=prefix, tags=[integration.name])
    mount_integration_routes(router, integration)
    app.include_router(router)

# Add weather geocoding endpoint (shared across all weather calendars)
app.include_router(geocode_router)
