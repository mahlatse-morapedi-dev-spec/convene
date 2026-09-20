"""Adds the organizer flag for whichever event the current URL points at."""

from events.models import Event


def event_role(request):
    match = getattr(request, "resolver_match", None)
    slug = match.kwargs.get("slug") if match else None
    if not slug:
        return {}
    event = Event.objects.filter(slug=slug).only("id").first()
    if not event:
        return {}
    return {"is_organizer": event.is_organizer(request.user)}
