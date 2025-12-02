from typing import List, Optional
from datetime import datetime, timedelta
import os

import requests
from fastapi import HTTPException

from base import CalendarBase, Event, IntegrationBase
from utils import make_slug


def get_weather_emoji(condition: str, description: str = "") -> str:
    """
    Map weather condition to appropriate emoji.
    
    Args:
        condition: Main weather condition (e.g., "Clear", "Clouds", "Rain")
        description: Detailed description (e.g., "light rain", "heavy snow")
    
    Returns:
        Emoji string for the weather condition
    """
    condition_lower = condition.lower()
    description_lower = description.lower()
    
    # Clear/Sunny
    if condition_lower in ["clear"]:
        return "☀️"
    
    # Clouds
    if condition_lower in ["clouds"]:
        if "few" in description_lower or "scattered" in description_lower:
            return "🌤️"  # Partly cloudy
        elif "broken" in description_lower:
            return "⛅"  # Partly cloudy
        else:
            return "☁️"  # Cloudy
    
    # Rain
    if condition_lower in ["rain", "drizzle"]:
        if "light" in description_lower or "drizzle" in description_lower:
            return "🌦️"  # Light rain
        elif "heavy" in description_lower or "extreme" in description_lower:
            return "🌧️"  # Heavy rain
        else:
            return "🌧️"  # Rain
    
    # Thunderstorm
    if condition_lower in ["thunderstorm"]:
        return "⛈️"
    
    # Snow
    if condition_lower in ["snow"]:
        if "light" in description_lower:
            return "🌨️"  # Light snow
        elif "heavy" in description_lower:
            return "❄️"  # Heavy snow
        else:
            return "❄️"  # Snow
    
    # Mist/Fog
    if condition_lower in ["mist", "fog", "haze"]:
        return "🌫️"
    
    # Dust/Sand
    if condition_lower in ["dust", "sand"]:
        return "🌪️"
    
    # Tornado
    if condition_lower in ["tornado"]:
        return "🌪️"
    
    # Squall
    if condition_lower in ["squall"]:
        return "💨"
    
    # Ash (volcanic)
    if condition_lower in ["ash"]:
        return "🌋"
    
    # Default
    return "🌡️"


class WeatherCalendar(CalendarBase):
    def fetch_events(
        self,
        location: str,
        api_key: Optional[str] = None,
        days: int = 14,
        units: str = "metric",
    ) -> List[Event]:
        """
        Fetch daily weather forecasts from OpenWeatherMap for a given location.

        Parameters:
        - location (str): City name (e.g., "New York, NY" or "London")
        - api_key (str, optional): OpenWeatherMap API key. If not provided, uses OPENWEATHERMAP_API_KEY environment variable.
        - days (int): Number of days to fetch (default 14, max 16 for free tier)
        - units (str): Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin" (default: "metric")
        """
        try:
            # Validate and normalize inputs
            if not location or not location.strip():
                raise HTTPException(status_code=400, detail="Location is required")
            
            # Get API key from parameter or environment variable
            if not api_key or not api_key.strip():
                api_key = os.getenv("OPENWEATHERMAP_API_KEY")
            
            if not api_key or not api_key.strip():
                raise HTTPException(status_code=500, detail="OpenWeatherMap API key not configured. Please set OPENWEATHERMAP_API_KEY environment variable or provide api_key parameter.")
            
            api_key = api_key.strip()
            if days < 1 or days > 16:
                days = min(max(days, 1), 16)  # Clamp to valid range
            
            location = location.strip()
            units = units.lower()
            if units not in ["metric", "imperial", "kelvin"]:
                units = "metric"

            # Step 1: Geocode location to get coordinates
            geocode_url = "https://api.openweathermap.org/geo/1.0/direct"
            geocode_params = {
                "q": location,
                "limit": 1,
                "appid": api_key,
            }
            
            geocode_response = requests.get(geocode_url, params=geocode_params, timeout=15)
            
            # Check for HTTP errors
            if geocode_response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid API key")
            if geocode_response.status_code == 429:
                raise HTTPException(status_code=429, detail="API rate limit exceeded")
            
            # Check response body for OpenWeatherMap error messages
            try:
                geocode_data = geocode_response.json()
            except:
                geocode_response.raise_for_status()
                raise HTTPException(status_code=500, detail="Invalid response from weather API")
            
            # OpenWeatherMap sometimes returns errors in JSON with 200 status
            if isinstance(geocode_data, dict):
                if "cod" in geocode_data and geocode_data["cod"] == "401":
                    raise HTTPException(status_code=401, detail=geocode_data.get("message", "Invalid API key"))
                if "cod" in geocode_data and geocode_data["cod"] == "429":
                    raise HTTPException(status_code=429, detail=geocode_data.get("message", "API rate limit exceeded"))
                if "message" in geocode_data and geocode_data.get("cod") != "200":
                    error_msg = geocode_data.get("message", "Unknown error")
                    error_code = int(geocode_data.get("cod", 500))
                    raise HTTPException(status_code=error_code, detail=f"Weather API error: {error_msg}")
            
            geocode_response.raise_for_status()
            
            if not geocode_data or len(geocode_data) == 0:
                raise HTTPException(status_code=404, detail=f"Location not found: {location}")
            
            lat = geocode_data[0]["lat"]
            lon = geocode_data[0]["lon"]
            city_name = geocode_data[0].get("name", location)
            country = geocode_data[0].get("country", "")
            # Use just city name for display (without country)
            location_display = city_name

            # Step 2: Fetch 5-day/3-hour forecast (free tier)
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                "lat": lat,
                "lon": lon,
                "units": units,
                "appid": api_key,
            }
            
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=15)
            
            # Check for HTTP errors
            if forecast_response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid API key")
            if forecast_response.status_code == 429:
                raise HTTPException(status_code=429, detail="API rate limit exceeded")
            
            # Check response body for OpenWeatherMap error messages
            try:
                forecast_data = forecast_response.json()
            except:
                forecast_response.raise_for_status()
                raise HTTPException(status_code=500, detail="Invalid response from weather API")
            
            # OpenWeatherMap sometimes returns errors in JSON with 200 status
            if isinstance(forecast_data, dict):
                if "cod" in forecast_data and forecast_data["cod"] == "401":
                    raise HTTPException(status_code=401, detail=forecast_data.get("message", "Invalid API key"))
                if "cod" in forecast_data and forecast_data["cod"] == "429":
                    raise HTTPException(status_code=429, detail=forecast_data.get("message", "API rate limit exceeded"))
                if "message" in forecast_data and forecast_data.get("cod") != "200":
                    error_msg = forecast_data.get("message", "Unknown error")
                    error_code = int(forecast_data.get("cod", 500))
                    raise HTTPException(status_code=error_code, detail=f"Weather API error: {error_msg}")
            
            forecast_response.raise_for_status()
            
            if "list" not in forecast_data:
                raise HTTPException(status_code=500, detail="Invalid forecast response format")

            # Step 3: Aggregate 3-hour forecasts into daily forecasts
            events: List[Event] = []
            temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
            wind_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"
            
            # Group forecasts by day
            daily_forecasts = {}
            for forecast in forecast_data["list"]:
                timestamp = forecast.get("dt", 0)
                if timestamp == 0:
                    continue
                
                forecast_dt = datetime.utcfromtimestamp(timestamp)
                day_key = forecast_dt.date()
                
                if day_key not in daily_forecasts:
                    daily_forecasts[day_key] = {
                        "forecasts": [],
                        "temps": [],
                        "humidities": [],
                        "wind_speeds": [],
                        "wind_degs": [],
                        "clouds": [],
                        "pressures": [],
                        "weather_conditions": [],
                    }
                
                daily_forecasts[day_key]["forecasts"].append(forecast)
                
                main = forecast.get("main", {})
                daily_forecasts[day_key]["temps"].append(main.get("temp", 0))
                daily_forecasts[day_key]["humidities"].append(main.get("humidity", 0))
                daily_forecasts[day_key]["pressures"].append(main.get("pressure", 0))
                
                wind = forecast.get("wind", {})
                daily_forecasts[day_key]["wind_speeds"].append(wind.get("speed", 0))
                daily_forecasts[day_key]["wind_degs"].append(wind.get("deg", 0))
                
                clouds = forecast.get("clouds", {})
                daily_forecasts[day_key]["clouds"].append(clouds.get("all", 0))
                
                weather = forecast.get("weather", [{}])[0]
                daily_forecasts[day_key]["weather_conditions"].append(weather)
            
            # Convert daily aggregates to events
            sorted_days = sorted(daily_forecasts.keys())[:days]
            
            for day_key in sorted_days:
                day_data = daily_forecasts[day_key]
                
                # Calculate daily averages and extremes
                temps = day_data["temps"]
                temp_min = min(temps) if temps else 0
                temp_max = max(temps) if temps else 0
                temp_avg = sum(temps) / len(temps) if temps else 0
                
                humidity_avg = sum(day_data["humidities"]) / len(day_data["humidities"]) if day_data["humidities"] else 0
                wind_speed_avg = sum(day_data["wind_speeds"]) / len(day_data["wind_speeds"]) if day_data["wind_speeds"] else 0
                clouds_avg = sum(day_data["clouds"]) / len(day_data["clouds"]) if day_data["clouds"] else 0
                pressure_avg = sum(day_data["pressures"]) / len(day_data["pressures"]) if day_data["pressures"] else 0
                
                # Get most common weather condition
                weather_conditions = day_data["weather_conditions"]
                if weather_conditions:
                    # Use the condition from the middle of the day (most representative)
                    mid_index = len(weather_conditions) // 2
                    primary_weather = weather_conditions[mid_index]
                    description = primary_weather.get("description", "").capitalize()
                    condition = primary_weather.get("main", "Unknown")
                else:
                    description = "Unknown"
                    condition = "Unknown"
                
                # Get average wind direction
                wind_degs = [d for d in day_data["wind_degs"] if d > 0]
                wind_deg_avg = sum(wind_degs) / len(wind_degs) if wind_degs else 0
                
                # Create start datetime (beginning of day in UTC)
                start_dt = datetime.combine(day_key, datetime.min.time()).replace(tzinfo=None)
                end_dt = start_dt + timedelta(days=1)
                
                # Get emoji for weather condition
                emoji = get_weather_emoji(condition, description)
                
                # Create title with emoji, temperature, and city name
                title = f"{emoji} {int(temp_avg)}{temp_unit} {location_display}"
                
                # Create detailed description
                desc_parts = [
                    f"Temperature: {int(temp_min)}{temp_unit} - {int(temp_max)}{temp_unit}",
                    f"Condition: {description}",
                    f"Humidity: {int(humidity_avg)}%",
                    f"Wind: {wind_speed_avg:.1f} {wind_unit}",
                    f"Clouds: {int(clouds_avg)}%",
                    f"Pressure: {int(pressure_avg)} hPa",
                ]
                if wind_deg_avg > 0:
                    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                    wind_dir = directions[int((wind_deg_avg + 11.25) / 22.5) % 16]
                    desc_parts.append(f"Wind Direction: {wind_dir}")
                
                description_text = " | ".join(desc_parts)
                
                # Create UID
                date_str = start_dt.strftime("%Y%m%d")
                location_slug = make_slug(location_display)
                uid = f"weather-{location_slug}-{date_str}"
                
                events.append(
                    Event(
                        uid=uid,
                        title=title,
                        start=start_dt,
                        end=end_dt,
                        all_day=True,
                        description=description_text,
                        location=location_display,
                    )
                )
            
            self.events = events
            return events
            
        except HTTPException:
            raise
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Weather API request failed: {str(e)}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch weather events: {str(e)}") from e


class WeatherIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        return None

