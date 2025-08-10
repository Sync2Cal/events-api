# API Endpoints

Sync2Cal exposes one endpoint per integration: `GET /<integration-id>/events`.

## Routing
- Prefix is derived from `integration.id` with underscores converted to hyphens.
  - Examples: `twitch -> /twitch`, `google_sheets -> /google-sheets`.
- Each endpoint is mounted via `mount_integration_routes(...)` and proxies to the corresponding `Calendar.fetch_events`.

## Query Parameters
- All `fetch_events` parameters of a provider are available as query params.
- An extra parameter is injected by the router:
  - `ics` (bool, default `true`):
    - `true`: returns `text/plain` ICS content
    - `false`: returns JSON list of `Event` objects

## JSON Event Schema
```json
{
  "uid": "string",
  "title": "string",
  "start": "ISO-8601 datetime",
  "end": "ISO-8601 datetime",
  "all_day": true,
  "description": "string",
  "location": "string",
  "extra": { "...": "provider-specific" }
}
```

## Examples

### JSON
```bash
curl "http://localhost:8000/imdb/events?ics=false&country=US&genre=all"
```
Response:
```json
[
  {
    "uid": "imdb-tt1234567",
    "title": "Some Movie",
    "start": "2025-06-27T08:00:00",
    "end": "2025-06-28T08:00:00",
    "all_day": true,
    "description": "Title: Some Movie | Genres: Action | Cast: ... | IMDb: https://www.imdb.com/title/tt1234567/",
    "location": "https://www.imdb.com/title/tt1234567/",
    "extra": {}
  }
]
```

### ICS
```bash
curl "http://localhost:8000/moviedb/events" -H "Accept: text/plain"
```
Response (excerpt):
```
BEGIN:VCALENDAR
VERSION:2.0
X-WR-CALNAME:MovieDB
BEGIN:VEVENT
SUMMARY:Some Movie
DTSTART;VALUE=DATE:20250627
DTEND;VALUE=DATE:20250628
UID:tmdb-somemovie-20250627
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
```

## OpenAPI
- Interactive docs are available at `/docs`.
- The `GET /<integration>/events` endpoint summary is shown as `Fetch events for <Name>`.
- The `ics` parameter is documented automatically.
