from fastapi import HTTPException
import os
from base import CalendarBase, Event, IntegrationBase
from typing import List
from datetime import datetime, timezone, timedelta
import gspread
from utils import make_slug


class GoogleSheetsCalendar(CalendarBase):
    def fetch_events(
        self,
        sheet_url: str,
    ) -> List[Event]:
        """
        Converts Google Sheet events to calendar events (Event objects).

        Requirements:
        - The first row of the sheet must contain headers with the following exact column names:
            name of event, description, location, start date, start time, end date, end time, all day event
        - Dates must be in YYYY-MM-DD format.
        - Times must be in 24-hour HH:MM format (UTC). Leave time fields empty for all-day events.
        - "all day event" must be either "true", "yes", or "1" (case-insensitive) for all-day events.
        - If "all day event" is anything else or left blank, the event is considered a timed event.
            - In that case, all of the following fields are required: start date, start time, end date, end time.
        - If an all-day event does not include an end date, it will be assumed to be a single-day event.

        Parameters:
        - sheet_url (str, required): The URL of the Google Sheet containing event data.

        Service Account Access:
        - Share view access of the Google Sheet with this email: sheets-acces@scrapper-466317.iam.gserviceaccount.com
        """
        try:
            try:
                sa_path = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE", "service_account.json")
                gc = gspread.service_account(filename=sa_path)
            except Exception as auth_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to authenticate Google service account: {auth_error}",
                ) from auth_error

            try:
                sh = gc.open_by_url(sheet_url)
                worksheet = sh.sheet1
                rows = worksheet.get_all_values()
            except gspread.exceptions.SpreadsheetNotFound:
                raise HTTPException(status_code=404, detail="Spreadsheet not found or access denied")
            except Exception as open_error:
                raise HTTPException(status_code=500, detail=str(open_error)) from open_error

            if not rows or len(rows) < 2:
                raise HTTPException(status_code=404, detail="Sheet is empty or missing data")

            header = [h.strip().lower() for h in rows[0]]
            data_rows = rows[1:]

            def is_all_day(value: str) -> bool:
                return (value or "").strip().lower() in ("yes", "true", "1")

            def parse_date(date_str: str) -> datetime:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

            def parse_datetime(date_str: str, time_str: str) -> datetime:
                combined = f"{date_str} {time_str}"
                return datetime.strptime(combined, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

            events: List[Event] = []
            for row in data_rows:
                try:
                    record = dict(zip(header, row))

                    all_day = is_all_day(record.get("all day event", ""))

                    if all_day:
                        start_dt = parse_date(record["start date"])  # midnight UTC
                        end_date_raw = (record.get("end date") or "").strip()
                        if end_date_raw:
                            end_dt = parse_date(end_date_raw) + timedelta(days=1)
                        else:
                            end_dt = start_dt + timedelta(days=1)
                    else:
                        start_dt = parse_datetime(record["start date"], record["start time"])  # UTC
                        end_dt = parse_datetime(record["end date"], record["end time"])  # UTC

                    name = record.get("name of event", "Untitled Event")
                    uid = f"sheet-{start_dt.strftime('%Y%m%dT%H%M')}-{make_slug(name, 20)}"

                    event = Event(
                        uid=uid,
                        title=name,
                        start=start_dt,
                        end=end_dt,
                        all_day=all_day,
                        description=record.get("description", ""),
                        location=record.get("location", ""),
                    )
                    events.append(event)

                except KeyError as missing:
                    # Missing required columns for this row; skip it
                    continue
                except Exception:
                    # Skip bad rows, continue processing others
                    continue

            if not events:
                raise HTTPException(status_code=404, detail="No valid events found")

            self.events = events
            return events

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}") from e


class GoogleSheetsIntegration(IntegrationBase):
    def fetch_calendars(self, *args, **kwargs):
        """
        Placeholder for multi-calendar support if needed later.
        """
        pass


