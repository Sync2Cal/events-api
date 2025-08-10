from typing import List, Optional, Union
from datetime import datetime, timedelta

from fastapi import HTTPException, Query

from base import CalendarBase, Event, IntegrationBase

# Reuse existing scraping/parsing helpers from the router module
from routers.investing import (
    resolve_dates,
    convert_names_to_ids,
    fetch_earnings,
    fetch_ipo_events,
    COUNTRY_MAP,
    SECTOR_MAP,
    IMPORTANCE_MAP,
)


class InvestingCalendar(CalendarBase):
    def fetch_events(
        self,
        kind: str = "earnings",
        country: List[Union[str, int]] = Query(default=[]),
        sector: List[Union[str, int]] = Query(default=[]),
        importance: List[Union[str, int]] = Query(default=[]),
        tab: str = "thisWeek",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Event]:
        """
        Fetch Investing.com events as calendar events.

        Parameters:
        - kind (str): "earnings" or "ipo". Defaults to "earnings".
        - country (List[str|int]): Names (case-insensitive) or IDs from COUNTRY_MAP.
        - sector (List[str|int]): Names or IDs (earnings only).
        - importance (List[str|int]): "low" | "medium" | "high" or IDs (earnings only).
        - tab (str): One of: "yesterday", "today", "tomorrow", "thisWeek", "nextWeek" (earnings only).
        - date_from/date_to (YYYY-MM-DD): Custom range (earnings only). Must be provided together.
        """
        try:
            events: List[Event] = []

            if kind.lower() == "earnings":
                from_date, to_date, current_tab = resolve_dates(tab, date_from, date_to)
                country_ids = convert_names_to_ids(country, COUNTRY_MAP, "country")
                sector_ids = convert_names_to_ids(sector, SECTOR_MAP, "sector")
                importance_ids = convert_names_to_ids(importance, IMPORTANCE_MAP, "importance")

                raw = fetch_earnings(
                    from_date, to_date, country_ids, sector_ids, importance_ids, current_tab
                )

                for e in raw:
                    start = datetime.strptime(e["date"], "%Y-%m-%d")
                    end = start + timedelta(days=1)

                    description = (
                        f"Company: {e['company']} | Country: {e['country']} | "
                        f"EPS (actual/forecast): {e['eps']['actual']} / {e['eps']['forecast']} | "
                        f"Revenue (actual/forecast): {e['revenue']['actual']} / {e['revenue']['forecast']} | "
                        f"Market Cap: {e['market_cap']} | Time: {e.get('time') or 'N/A'}"
                    )

                    events.append(
                        Event(
                            uid=f"inv-earnings-{e['company'].replace(' ', '').lower()}-{e['date']}",
                            title=f"Earnings – {e['company']}",
                            start=start,
                            end=end,
                            all_day=True,
                            description=description,
                            location="",
                        )
                    )

            elif kind.lower() == "ipo":
                # For IPOs, only country filter is used
                country_ids = convert_names_to_ids(country, COUNTRY_MAP, "country") if country else []
                raw = fetch_ipo_events(country_ids)

                for e in raw:
                    start = datetime.strptime(e["date"], "%Y-%m-%d")
                    end = start + timedelta(days=1)
                    description = (
                        f"Company: {e['company']} | Country: {e['country']} | "
                        f"Exchange: {e['exchange']} | IPO Value: {e['ipo_value']} | "
                        f"IPO Price: {e['ipo_price']} | Last: {e['last']}"
                    )

                    events.append(
                        Event(
                            uid=f"inv-ipo-{e['company'].replace(' ', '').lower()}-{e['date']}",
                            title=f"IPO – {e['company']}",
                            start=start,
                            end=end,
                            all_day=True,
                            description=description,
                            location="https://www.investing.com/ipo-calendar/",
                        )
                    )

            else:
                raise HTTPException(status_code=400, detail="Invalid kind. Use 'earnings' or 'ipo'.")

            self.events = events
            return events
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


class InvestingIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        """
        Placeholder for future multi-calendar support.
        """
        return None


