from typing import List, Optional, Union
from datetime import datetime, timedelta

from fastapi import HTTPException, Query

from base import CalendarBase, Event, IntegrationBase

# Inlined helpers and constants (moved from routers/investing.py)
import requests
from bs4 import BeautifulSoup
from html import unescape

# Earnings constants
EARNINGS_URL = "https://www.investing.com/earnings-calendar/Service/getCalendarFilteredData"
EARNINGS_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.investing.com/earnings-calendar/",
}

# IPO constants
IPO_URL = "https://www.investing.com/ipo-calendar/Service/getCalendarFilteredData"
IPO_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.investing.com/ipo-calendar/",
}

# Maps
COUNTRY_MAP = {
    "argentina": 29,
    "australia": 25,
    "austria": 54,
    "bahrain": 145,
    "bangladesh": 47,
    "belgium": 34,
    "bosnia-herzegovina": 174,
    "botswana": 163,
    "brazil": 32,
    "bulgaria": 70,
    "canada": 6,
    "chile": 27,
    "china": 37,
    "colombia": 122,
    "costa rica": 15,
    "cote d'ivoire": 78,
    "croatia": 113,
    "cyprus": 107,
    "czech republic": 55,
    "denmark": 24,
    "egypt": 59,
    "estonia": 89,
    "euro zone": 72,
    "finland": 71,
    "france": 22,
    "germany": 17,
    "greece": 51,
    "hong kong": 39,
    "hungary": 93,
    "iceland": 106,
    "india": 14,
    "indonesia": 48,
    "iraq": 66,
    "ireland": 33,
    "israel": 23,
    "italy": 10,
    "jamaica": 119,
    "japan": 35,
    "jordan": 92,
    "kazakhstan": 102,
    "kenya": 57,
    "kuwait": 94,
    "latvia": 97,
    "lebanon": 68,
    "lithuania": 96,
    "luxembourg": 103,
    "malawi": 111,
    "malaysia": 42,
    "malta": 109,
    "mauritius": 188,
    "mexico": 7,
    "mongolia": 139,
    "montenegro": 247,
    "morocco": 105,
    "namibia": 172,
    "netherlands": 21,
    "new zealand": 43,
    "nigeria": 20,
    "norway": 60,
    "oman": 87,
    "pakistan": 44,
    "palestinian territory": 193,
    "peru": 125,
    "philippines": 45,
    "poland": 53,
    "portugal": 38,
    "qatar": 170,
    "romania": 100,
    "russia": 56,
    "rwanda": 80,
    "saudi arabia": 52,
    "serbia": 238,
    "singapore": 36,
    "slovakia": 90,
    "slovenia": 112,
    "south africa": 110,
    "south korea": 11,
    "spain": 26,
    "sri lanka": 162,
    "sweden": 9,
    "switzerland": 12,
    "taiwan": 46,
    "tanzania": 85,
    "thailand": 41,
    "tunisia": 202,
    "türkiye": 63,
    "uganda": 123,
    "ukraine": 61,
    "united arab emirates": 143,
    "united kingdom": 4,
    "united states": 5,
    "venezuela": 138,
    "vietnam": 178,
    "zambia": 84,
    "zimbabwe": 75,
}

SECTOR_MAP = {
    "energy": 24,
    "basic materials": 25,
    "industrials": 26,
    "consumer cyclicals": 27,
    "consumer non-cyclicals": 28,
    "financials": 29,
    "healthcare": 30,
    "technology": 31,
    "utilities": 32,
    "real estate": 33,
    "institutions, associations & organizations": 34,
    "government activity": 35,
    "academic and educational services": 36,
}

IMPORTANCE_MAP = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def clean(text: str) -> str:
    return (
        unescape(text)
        .replace("\xa0", " ")
        .replace("/", "")
        .replace("<\\/td>", "")
        .replace("\\/", "")
        .strip()
    )


def resolve_dates(tab: Optional[str], date_from: Optional[str], date_to: Optional[str]):
    if date_from and date_to:
        return date_from, date_to, "custom"
    valid_tabs = {"yesterday", "today", "tomorrow", "thisWeek", "nextWeek"}
    if tab in valid_tabs:
        return None, None, tab
    raise HTTPException(status_code=400, detail="Invalid tab or missing date range.")


def convert_names_to_ids(items: List[Union[str, int]], mapping: dict, label: str) -> List[int]:
    ids: List[int] = []
    for item in items:
        if isinstance(item, int):
            ids.append(item)
        else:
            key = str(item).strip().lower()
            if key in mapping:
                ids.append(mapping[key])
            else:
                raise HTTPException(status_code=400, detail=f"Invalid {label}: {item}")
    return ids


def build_earnings_payload(date_from, date_to, countries, sectors, importance, current_tab):
    payload = {
        "submitFilters": "1",
        "limit_from": "0",
        "currentTab": current_tab,
    }
    if current_tab == "custom":
        payload["dateFrom"] = date_from
        payload["dateTo"] = date_to
    if countries:
        payload["country[]"] = [str(cid) for cid in countries]
    if sectors:
        payload["sector[]"] = [str(sid) for sid in sectors]
    if importance:
        payload["importance[]"] = [str(imp) for imp in importance]
    return payload


def parse_earnings(html: str, fallback_date: str):
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr")
    results = []
    current_date = fallback_date
    for row in rows:
        day_td = row.find("td", class_="theDay")
        if day_td:
            try:
                current_date = datetime.strptime(
                    day_td.text.strip(), "%A, %B %d, %Y"
                ).strftime("%Y-%m-%d")
            except ValueError:
                continue
            continue
        tds = row.find_all("td")
        if len(tds) < 6:
            continue
        country_span = tds[0].find("span", title=True)
        country = country_span["title"] if country_span else "Unknown"
        company_td = tds[1]
        name_span = company_td.find("span")
        ticker_a = company_td.find("a")
        name = name_span.text.strip() if name_span else ""
        ticker = ticker_a.text.strip() if ticker_a else ""
        if not name and not ticker:
            parts = list(company_td.stripped_strings)
            company = " ".join(parts) if parts else "Unknown"
        else:
            company = f"{name} ({ticker})" if ticker else name
        eps = {
            "actual": clean(tds[2].text),
            "forecast": clean(tds[3].text),
        }
        revenue = {
            "actual": clean(tds[4].text),
            "forecast": clean(tds[5].text),
        }
        market_cap = clean(tds[6].text) if len(tds) > 6 else "--"
        time = "N/A"
        if len(tds) > 7:
            span = tds[7].find("span", attrs={"data-tooltip": True})
            if span and span.has_attr("data-tooltip"):
                time = span["data-tooltip"].strip()
        results.append(
            {
                "date": current_date,
                "company": company,
                "country": country,
                "eps": eps,
                "revenue": revenue,
                "market_cap": market_cap,
                "time": time,
            }
        )
    return results


def fetch_earnings(date_from, date_to, countries, sectors, importance, current_tab):
    payload = build_earnings_payload(
        date_from, date_to, countries, sectors, importance, current_tab
    )
    response = requests.post(EARNINGS_URL, headers=EARNINGS_HEADERS, data=payload, timeout=20)
    response.raise_for_status()
    html = response.json()["data"]
    clean_html = unescape(html)
    return parse_earnings(clean_html, date_from or "1970-01-01")


def build_ipo_payload(countries: List[int]) -> dict:
    payload = {
        "submitFilters": "1",
        "limit_from": "0",
        "currentTab": "upcoming",
    }
    if countries:
        payload["country[]"] = [str(c) for c in countries]
    return payload


def parse_ipo_html(html: str):
    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")
    results = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 5:
            continue
        date_str = clean(tds[0].text)
        try:
            date = datetime.strptime(date_str, "%b %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        country_span = tds[1].find("span", title=True)
        country = country_span["title"] if country_span else "Unknown"
        name_span = tds[1].find("span", class_="elp")
        name = name_span["title"] if name_span else "Unknown"
        ticker_a = tds[1].find("a")
        ticker = ticker_a.text.strip() if ticker_a else ""
        exchange = clean(tds[2].text)
        ipo_value_a = clean(tds[3].text)
        ipo_value = ipo_value_a if ipo_value_a else "-"
        ipo_price = clean(tds[4].text)
        last = clean(tds[5].text)
        company = f"{name} ({ticker})" if ticker else name
        results.append(
            {
                "date": date,
                "company": company,
                "country": country,
                "exchange": exchange,
                "ipo_value": ipo_value,
                "ipo_price": ipo_price,
                "last": last,
            }
        )
    return results


def fetch_ipo_events(countries: List[int]) -> List[dict]:
    payload = build_ipo_payload(countries)
    response = requests.post(IPO_URL, headers=IPO_HEADERS, data=payload, timeout=20)
    response.raise_for_status()
    html = unescape(response.json()["data"])
    return parse_ipo_html(html)


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


