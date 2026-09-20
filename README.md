# Convene

An event platform in Django, built along the same functional lines as Whova: one
event record feeding three surfaces — an attendee view, an organizer view, and an
exhibitor view.

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations events attendees engagement exhibitors
python manage.py migrate
python manage.py seed_demo          # builds a full demo conference
python manage.py runserver
```

Then open http://127.0.0.1:8000/. The demo event lives at `/e/safari-datacon-2026/`.
Sign in as `organizer` / `convene123` to see the manage and check-in views; that
account is also a superuser, so `/admin/` works.

Run the tests with `python manage.py test`.

## How it's laid out

| App | Owns |
| --- | --- |
| `events` | `Event`, `Track`, `Session`, `Speaker`, `Announcement`, the agenda and the organizer dashboard |
| `attendees` | `TicketType`, `Registration`, `AttendeeProfile`, `AgendaItem`, `Message`, registration and check-in |
| `engagement` | `Poll`, `Question`, `Topic`/`Post`, `SessionFeedback` — everything attendees produce |
| `exhibitors` | `Exhibitor`, `Lead`, stand pages and lead capture |

`Registration` is the hinge. It is the ticket, the directory entry, the author of
every question and post, and the thing an exhibitor captures as a lead — so a
person exists once per event and everything else points at that row.
`attendees.services.get_registration()` is the single place that resolves the
signed-in user to their registration for the event in the URL.

Permissions are deliberately simple: `Event.is_organizer(user)` gates the manage
and check-in views, exhibitor staff are a many-to-many onto `Registration`, and
everything else is either public or requires a registration.

## What's here

- Registration with multiple ticket types, quantity limits and duplicate-email guarding
- Agenda with day grouping, track and keyword filters, personal schedule with clash detection
- Session pages with audience Q&A (upvotable, optionally anonymous), live polls with results, and post-session ratings
- Attendee directory with visibility opt-out, interest-based suggestions and direct messages
- Community board with discussion, meet-up and lift-share threads
- Exhibitor pages, attendee-initiated detail sharing, badge-code lead capture and CSV export
- Organizer dashboard: registrations, check-ins, most-saved sessions, engagement counts
- Desk check-in by badge code or email

## What's stubbed, and what you'd add next

- **Payments.** `TicketType.price` exists but nothing charges a card. Drop in Stripe Checkout and mark `Registration.status` on the webhook.
- **QR codes.** Check-in matches a typed badge code. `qrcode` is in requirements; render `Registration.reference` as a QR on the ticket and point a scanner at a URL that stamps `checked_in_at`.
- **Real-time.** Polls and Q&A are request-response. Django Channels over the same models would make them live without schema changes.
- **Email.** No confirmations are sent. Wire `django.core.mail` into the registration view.
- **Streaming.** `Session.stream_url` just links out — embed Zoom or an HLS player if you want it in-page.
- **Multi-tenancy.** Everything is scoped by event, but there's no organization layer above it. Add one before you sell this to more than one customer.

## Notes on the code

- SQLite by default; swap `DATABASES` for Postgres before any real load.
- `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` read from the environment.
- Timezone is set to `Africa/Johannesburg` with `USE_TZ = True`; `Event.timezone_name` is stored per event but display currently uses the project timezone.
- Templates are plain Django with one stylesheet — no build step, no JS framework.
