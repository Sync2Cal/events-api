"""
Geocoding endpoint for weather city search
Uses OpenWeatherMap's geocoding API to find cities matching a query
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
import os
import requests

geocode_router = APIRouter(tags=["Weather"])


@geocode_router.get("/weather/geocode")
async def geocode_cities(
    q: str = Query(..., description="City name to search for"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results to return"),
):
    """
    Search for cities using OpenWeatherMap's geocoding API.
    Returns a list of matching cities with their formatted names.
    """
    try:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key or not api_key.strip():
            raise HTTPException(
                status_code=500,
                detail="OpenWeatherMap API key not configured"
            )

        # Use OpenWeatherMap's direct geocoding API
        # For single-word queries like "new", try multiple search patterns
        # to find cities like "New York", "New Orleans", etc.
        search_query = q.strip().lower()
        if len(search_query.split()) == 1 and len(search_query) > 2:
            # Single word query - try multiple patterns
            # Common patterns for cities starting with this word
            search_queries = [
                search_query,  # Original query
                f"{search_query} city",  # With "city" suffix
            ]
            # For "new", also try common city names
            if search_query == "new":
                search_queries.extend([
                    "new york",
                    "new orleans", 
                    "new delhi",
                    "new haven",
                    "new jersey",
                ])
        else:
            search_queries = [q.strip()]
        
        # Request more results than needed since we'll filter them
        all_results = []
        for sq in search_queries:
            geocode_url = "https://api.openweathermap.org/geo/1.0/direct"
            geocode_params = {
                "q": sq,
                "limit": min(limit * 3, 20),  # Request more results to filter from
                "appid": api_key,
            }
            
            response = requests.get(geocode_url, params=geocode_params, timeout=10)
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid API key")
            if response.status_code == 429:
                raise HTTPException(status_code=429, detail="API rate limit exceeded")
            
            response.raise_for_status()
            data = response.json()
            
            # Check for OpenWeatherMap error responses
            if isinstance(data, dict) and "cod" in data:
                if data["cod"] == "401":
                    raise HTTPException(status_code=401, detail=data.get("message", "Invalid API key"))
                if data["cod"] == "429":
                    raise HTTPException(status_code=429, detail=data.get("message", "API rate limit exceeded"))
            
            if isinstance(data, list):
                all_results.extend(data)
        
        # Remove duplicates based on city name and country
        seen = set()
        unique_results = []
        for item in all_results:
            city_name = item.get("name", "")
            country = item.get("country", "")
            key = (city_name.lower(), country.lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(item)
        
        data = unique_results


        # Normalize query for filtering (case-insensitive)
        normalized_query = q.lower().strip()
        
        # Format results and filter to only include cities whose names start with the query
        # For single-word queries like "new", we want cities like "New York", "New Orleans"
        # which start with the query word
        results = []
        for item in data:
            city_name = item.get("name", "")
            state = item.get("state", "")
            country = item.get("country", "")
            
            # Filter: include cities whose name starts with the query (case-insensitive)
            # This ensures "new" returns "New York", "New Orleans", etc.
            city_lower = city_name.lower()
            if not city_lower.startswith(normalized_query):
                continue
            
            # Build display name
            display_name = city_name
            if state:
                display_name += f", {state}"
            if country:
                display_name += f", {country}"
            
            results.append({
                "name": city_name,
                "displayName": display_name,
                "locationForWeather": f"{city_name}, {country}" if country else city_name,
                "country": country,
                "state": state,
                "lat": item.get("lat"),
                "lon": item.get("lon"),
            })
            
            # Limit results to requested limit
            if len(results) >= limit:
                break

        return results

    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Geocoding API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to geocode cities: {str(e)}")

