from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import uuid
import re

def make_slug(text: str, max_length: int = 50) -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text: The text to convert to a slug
        max_length: Maximum length of the slug (default: 50)
    
    Returns:
        str: URL-friendly slug
    """
    if not text:
        return ""
    
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug

def generate_ics(
    events: List[Dict],
    calendar_name: str,
    calendar_description: Optional[str] = None,
    timezone: str = "UTC"
) -> str:
    """
    Generate an ICS calendar file content from a list of events.
    
    Args:
        events: List of event dictionaries. Each event should have:
            - name (str): Event name/title
            - begin (Union[str, datetime]): Start date/time
            - end (Optional[Union[str, datetime]]): End date/time (optional for all-day events)
            - description (Optional[str]): Event description
            - location (Optional[str]): Event location
            - uid (Optional[str]): Unique identifier for the event
            - all_day (Optional[bool]): Whether the event is all-day (defaults to False)
            - categories (Optional[List[str]]): List of categories for the event
            - url (Optional[str]): URL associated with the event
            - status (Optional[str]): Event status (e.g., "CONFIRMED", "TENTATIVE", "CANCELLED")
        calendar_name: Name of the calendar
        calendar_description: Optional description of the calendar
        timezone: Timezone for the calendar (defaults to UTC)
    
    Returns:
        str: ICS calendar content
    """
    def format_datetime(dt: Union[str, datetime], is_date: bool = False) -> str:
        if isinstance(dt, str):
            if 'T' not in dt and len(dt) == 10:
                dt = datetime.fromisoformat(dt)
            else:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        if is_date:
            return dt.strftime("%Y%m%d")
        return dt.strftime("%Y%m%dT%H%M%SZ")

    def escape_text(text: str) -> str:
        """Escape special characters in text fields."""
        return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n").replace("\r", "")

    def fold_line(line: str) -> str:
        """Fold long lines according to RFC 5545 (75 character limit)."""
        if len(line) <= 75:
            return line
        
        folded_lines = []
        while len(line) > 75:
            break_point = 75
            if line[break_point-1:break_point+1] == '\\\\':
                break_point -= 1
            elif line[break_point-2:break_point] == '\\\\':
                break_point -= 2
            
            folded_lines.append(line[:break_point])
            line = ' ' + line[break_point:]
            
        folded_lines.append(line)
        return '\r\n'.join(folded_lines)

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Calendar Generator//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_text(calendar_name)}",
        f"X-WR-TIMEZONE:{timezone}"
    ]
    
    if calendar_description:
        ics_content.append(f"X-WR-CALDESC:{escape_text(calendar_description)}")

    for event in events:
        event_lines = ["BEGIN:VEVENT"]
        
        name = event.get('name', 'Untitled Event')
        begin = event.get('begin')
        if not begin:
            continue

        is_all_day = event.get('all_day', False)
        if is_all_day:
            end_date = event.get('end')
            if not end_date:
                if isinstance(begin, str):
                    begin_dt = datetime.fromisoformat(begin) if 'T' not in begin and len(begin) == 10 else datetime.fromisoformat(begin.replace('Z', '+00:00'))
                else:
                    begin_dt = begin
                end_dt = begin_dt + timedelta(days=1)
                end_date = end_dt.strftime("%Y-%m-%d")
            
            event_lines.extend([
                f"DTSTART;VALUE=DATE:{format_datetime(begin, is_date=True)}",
                f"DTEND;VALUE=DATE:{format_datetime(end_date, is_date=True)}"
            ])
        else:
            event_lines.extend([
                f"DTSTART:{format_datetime(begin)}",
                f"DTEND:{format_datetime(event.get('end', begin))}"
            ])
        
        if event.get('description'):
            event_lines.append(f"DESCRIPTION:{escape_text(event['description'])}")
        if event.get('location'):
            event_lines.append(f"LOCATION:{escape_text(event['location'])}")
        if event.get('url'):
            event_lines.append(f"URL:{event['url']}")
        if event.get('status'):
            event_lines.append(f"STATUS:{event['status']}")
        if event.get('categories') and isinstance(event['categories'], list):
            categories_str = ','.join(str(cat) for cat in event['categories'] if cat)
            if categories_str:
                event_lines.append(f"CATEGORIES:{categories_str}")
            
        uid = event.get('uid', str(uuid.uuid4()))
        event_lines.extend([
            f"UID:{uid}",
            f"DTSTAMP:{format_datetime(datetime.utcnow())}",
            f"SUMMARY:{escape_text(name)}",
            "END:VEVENT"
        ])
        
        ics_content.extend(event_lines)

    ics_content.append("END:VCALENDAR")
    
    folded_lines = []
    for line in ics_content:
        folded_lines.append(fold_line(line))
    
    return "\r\n".join(folded_lines) 