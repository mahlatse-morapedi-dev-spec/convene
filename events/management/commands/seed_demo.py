"""Create a demo event with sessions, attendees, threads and exhibitors.

    python manage.py seed_demo

Re-running wipes the demo event and rebuilds it.
"""

import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendees.models import AgendaItem, AttendeeProfile, Registration, TicketType
from engagement.models import Poll, PollOption, PollVote, Post, Question, QuestionUpvote, Topic
from events.models import Announcement, Event, Session, Speaker, Track
from exhibitors.models import Exhibitor, Lead

SLUG = "safari-datacon-2026"

TRACKS = [
    ("Applied machine learning", "#0e5a54"),
    ("Data engineering", "#7a4b86"),
    ("Policy and ethics", "#a8730b"),
]

SPEAKERS = [
    ("Naledi Mokoena", "Principal data scientist", "Standard Bank"),
    ("Tariq Patel", "Head of platform", "Yoco"),
    ("Anneke van Wyk", "Research fellow", "Wits University"),
    ("Chidi Okonkwo", "Staff engineer", "Flutterwave"),
    ("Grace Wanjiru", "Policy lead", "Kenya ICT Authority"),
    ("Jaco Pretorius", "Founder", "Mesh Analytics"),
]

SESSION_TITLES = [
    ("Fraud models that survive contact with production", 0),
    ("Streaming pipelines on a small team's budget", 1),
    ("What the POPIA amendments mean for model training", 2),
    ("Feature stores: worth it, or premature?", 1),
    ("Evaluating LLMs without a benchmark that fits", 0),
    ("Data sovereignty across SADC", 2),
    ("From notebook to service in an afternoon", 1),
    ("Forecasting demand with sparse history", 0),
    ("Consent, collection and the grey middle", 2),
]

ATTENDEES = [
    ("Sipho Dlamini", "Nedbank", "Analytics manager", "fraud, forecasting, policy"),
    ("Refilwe Mahlangu", "Discovery", "Data scientist", "machine learning, health data"),
    ("Yusuf Adams", "Takealot", "Engineering lead", "data engineering, streaming"),
    ("Lerato Sithole", "UCT", "PhD candidate", "machine learning, ethics"),
    ("Daniel Oduya", "Safaricom", "Platform engineer", "streaming, data engineering"),
    ("Michelle Botha", "Old Mutual", "Head of data", "policy, governance, forecasting"),
    ("Kabelo Nkosi", "Independent", "Consultant", "machine learning, forecasting"),
    ("Fatima Ismail", "Wits University", "Lecturer", "ethics, policy, health data"),
    ("Pieter Steyn", "Mesh Analytics", "CTO", "data engineering, streaming"),
    ("Zanele Khumalo", "City of Johannesburg", "Data officer", "policy, governance"),
]

TOPICS = [
    ("discussion", "Anyone working on fraud detection at low transaction volumes?"),
    ("rideshare", "Lift from Pretoria on the Tuesday morning?"),
    ("meetup", "Informal dinner for people doing public-sector data"),
]

EXHIBITORS = [
    ("Yoco", "platinum", "Payments infrastructure for African businesses.", "A1"),
    ("Mesh Analytics", "gold", "Managed feature stores and pipelines.", "A4"),
    ("Cape Cloud", "silver", "Regional hosting with data residency guarantees.", "B2"),
    ("Karoo Data Institute", "exhibitor", "Short courses and certification.", "C7"),
    ("Umoja Labs", "exhibitor", "Open-source tooling for public data.", "C9"),
]


class Command(BaseCommand):
    help = "Create (or rebuild) the demo event."

    def handle(self, *args, **options):
        random.seed(7)
        Event.objects.filter(slug=SLUG).delete()

        organizer, created = User.objects.get_or_create(
            username="organizer", defaults={"email": "organizer@example.com"}
        )
        if created:
            organizer.set_password("convene123")
            organizer.is_staff = True
            organizer.is_superuser = True
            organizer.save()

        start = timezone.localdate() + timedelta(days=1)
        event = Event.objects.create(
            name="Safari DataCon 2026",
            slug=SLUG,
            tagline="Three days on data practice across the continent.",
            description=(
                "Safari DataCon brings together practitioners working on data "
                "infrastructure, applied machine learning and data policy. Two "
                "tracks of talks, one of workshops, and a lot of hallway."
            ),
            venue="Sandton Convention Centre",
            city="Johannesburg",
            starts_on=start,
            ends_on=start + timedelta(days=2),
            is_published=True,
        )
        event.organizers.add(organizer)

        tracks = [Track.objects.create(event=event, name=n, colour=c) for n, c in TRACKS]
        speakers = [
            Speaker.objects.create(
                event=event,
                full_name=n,
                job_title=t,
                organization=o,
                bio=f"{n} works on data problems at {o}.",
            )
            for n, t, o in SPEAKERS
        ]

        tz = timezone.get_current_timezone()
        sessions = []
        for index, (title, track_index) in enumerate(SESSION_TITLES):
            day = start + timedelta(days=index // 3)
            hour = 9 + (index % 3) * 3
            begins = datetime.combine(day, time(hour, 0), tzinfo=tz)
            session = Session.objects.create(
                event=event,
                track=tracks[track_index],
                title=title,
                abstract=(
                    "A practitioner's account of what worked, what broke, and what "
                    "the team would do differently. Time for questions at the end."
                ),
                kind=Session.KEYNOTE if index == 0 else Session.TALK,
                room=f"Hall {chr(65 + index % 3)}",
                starts_at=begins,
                ends_at=begins + timedelta(minutes=45),
                capacity=random.choice([80, 120, 250]),
            )
            session.speakers.add(random.choice(speakers))
            sessions.append(session)

        # Nudge one session to be live right now so the "on now" rail has content.
        live = sessions[0]
        live.starts_at = timezone.now() - timedelta(minutes=10)
        live.ends_at = timezone.now() + timedelta(minutes=35)
        live.save()

        Announcement.objects.create(
            event=event,
            title="Registration opens at 08:00",
            body="Collect your badge in the main foyer. Coffee is on the mezzanine.",
            is_pinned=True,
            created_by=organizer,
        )

        standard = TicketType.objects.create(
            event=event,
            name="Standard",
            description="Full access to all three days.",
            price=Decimal("2450.00"),
            quantity=400,
        )
        student = TicketType.objects.create(
            event=event,
            name="Student",
            description="Valid student card required at the desk.",
            price=Decimal("450.00"),
            quantity=100,
        )

        registrations = []
        for name, org, role, interests in ATTENDEES:
            ticket = student if "University" in org or "PhD" in role else standard
            registration = Registration.objects.create(
                event=event,
                ticket_type=ticket,
                full_name=name,
                email=f"{name.split()[0].lower()}@example.com",
                organization=org,
                job_title=role,
            )
            AttendeeProfile.objects.create(
                registration=registration,
                headline=f"{role} at {org}",
                bio=f"Working mostly on {interests.split(',')[0].strip()} at the moment.",
                interests=interests,
            )
            registrations.append(registration)

        # Give the organizer a registration too, so they can use attendee features.
        organizer_reg = Registration.objects.create(
            event=event,
            user=organizer,
            ticket_type=standard,
            full_name="Event Organizer",
            email="organizer@example.com",
            organization="Safari DataCon",
            job_title="Programme chair",
        )
        AttendeeProfile.objects.create(
            registration=organizer_reg,
            headline="Programme chair",
            interests="policy, machine learning",
        )
        registrations.append(organizer_reg)

        for registration in registrations:
            for session in random.sample(sessions, random.randint(2, 5)):
                AgendaItem.objects.get_or_create(
                    registration=registration, session=session
                )

        poll = Poll.objects.create(
            session=sessions[0],
            question="What's your biggest blocker in production ML?",
        )
        options = [
            PollOption.objects.create(poll=poll, text=text, position=i)
            for i, text in enumerate(
                ["Data quality", "Monitoring", "Stakeholder buy-in", "Compute cost"]
            )
        ]
        for registration in registrations[:8]:
            PollVote.objects.create(
                option=random.choice(options), registration=registration
            )

        prompts = [
            "How do you handle label delay when fraud is confirmed weeks later?",
            "What did you use for monitoring, and would you pick it again?",
            "Did legal push back on any of the features you wanted to use?",
        ]
        for registration, body in zip(registrations, prompts):
            question = Question.objects.create(
                session=sessions[0], registration=registration, body=body
            )
            for voter in random.sample(registrations, random.randint(1, 6)):
                QuestionUpvote.objects.get_or_create(
                    question=question, registration=voter
                )

        for kind, title in TOPICS:
            topic = Topic.objects.create(
                event=event,
                kind=kind,
                title=title,
                created_by=random.choice(registrations),
            )
            for registration in random.sample(registrations, 3):
                Post.objects.create(
                    topic=topic,
                    registration=registration,
                    body="Interested — count me in. Happy to help organize.",
                )

        for name, tier, blurb, booth in EXHIBITORS:
            exhibitor = Exhibitor.objects.create(
                event=event,
                name=name,
                tier=tier,
                blurb=blurb,
                booth_number=booth,
                description=blurb,
            )
            for registration in random.sample(registrations, random.randint(1, 4)):
                Lead.objects.get_or_create(
                    exhibitor=exhibitor, registration=registration
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Built {event.name} at /e/{event.slug}/\n"
                "Organizer login: organizer / convene123"
            )
        )
