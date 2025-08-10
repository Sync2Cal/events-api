from typing import Any, Dict, List
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
import inspect

from .integration import IntegrationBase
from .models import Event
from utils import generate_ics


def mount_integration_routes(router: APIRouter, integration: IntegrationBase):
    """
    Mounts the fetch_events route for the integration without inspecting its signature.
    Creates a wrapper function to avoid exposing 'self' parameter in FastAPI.
    """

    def fetch_events_wrapper(*args, **kwargs):
        ics = kwargs.pop("ics", True)
        calendar_instance = integration.calendar_class(
            name=integration.name,
            id=integration.id,
            icon="",
            events=[],
        )
        events = calendar_instance.fetch_events(*args, **kwargs)
        if ics:
            ics_events: List[Dict[str, Any]] = []
            for ev in events:
                ics_events.append(
                    {
                        "name": ev.title,
                        "begin": ev.start,
                        "end": ev.end,
                        "description": ev.description,
                        "location": ev.location,
                        "uid": ev.uid,
                        "all_day": ev.all_day,
                        "status": "CONFIRMED",
                    }
                )
            ics_text = generate_ics(events=ics_events, calendar_name=integration.name)
            return PlainTextResponse(ics_text, media_type="text/plain")
        return events

    original_method = integration.calendar_class.fetch_events
    sig = inspect.signature(original_method)

    fetch_events_wrapper.__doc__ = getattr(original_method, "__doc__", None)

    new_params = [param for name, param in sig.parameters.items() if name != "self"]
    ics_param = inspect.Parameter(
        "ics", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, default=True, annotation=bool
    )
    new_params.append(ics_param)
    new_sig = sig.replace(parameters=new_params)
    fetch_events_wrapper.__signature__ = new_sig
    fetch_events_wrapper.__annotations__ = getattr(original_method, "__annotations__", {})
    fetch_events_wrapper.__annotations__["ics"] = bool

    if "self" in fetch_events_wrapper.__annotations__:
        del fetch_events_wrapper.__annotations__["self"]

    base_doc = getattr(original_method, "__doc__", "") or ""
    fetch_events_wrapper.__doc__ = (
        base_doc
        + "\n\nAdditional parameters:\n- ics (bool, default True): If true, returns an ICS file (text/calendar) instead of JSON events."
    )

    router.add_api_route(
        "/events",
        fetch_events_wrapper,
        methods=["GET"],
        summary=f"Fetch events for {integration.name}",
    )


