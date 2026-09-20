"""Helpers shared across apps for resolving the current attendee."""

from attendees.models import Registration


def get_registration(request, event):
    """Return the signed-in user's confirmed registration for this event, or None."""
    if not request.user.is_authenticated:
        return None
    return (
        Registration.objects.filter(event=event, user=request.user)
        .exclude(status=Registration.CANCELLED)
        .select_related("profile", "ticket_type")
        .first()
    )
