from datetime import date
from events.models import Event

Event.objects.bulk_create([
    Event(
        name="Pretoria Tech Summit 2026",
        slug="pretoria-tech-summit-2026",
        city="Pretoria",
        venue="SunBet Arena",
        starts_on=date(2026, 10, 15),
        ends_on=date(2026, 10, 16),
        is_published=True,
    ),
    Event(
        name="Code Blue Film Festival",
        slug="code-blue-film-festival",
        city="Pretoria",
        venue="State Theatre",
        starts_on=date(2026, 11, 20),
        ends_on=date(2026, 11, 22),
        is_published=True,
    ),
    Event(
        name="Johannesburg Startup Week",
        slug="johannesburg-startup-week",
        city="Johannesburg",
        venue="Sandton Convention Centre",
        starts_on=date(2027, 2, 8),
        ends_on=date(2027, 2, 12),
        is_published=False,
    ),
])
print("successfully created events")