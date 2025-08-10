from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class Event:
    uid: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False
    description: str = ""
    location: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


