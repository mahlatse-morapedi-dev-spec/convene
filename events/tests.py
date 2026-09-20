from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from attendees.models import AgendaItem, AttendeeProfile, Registration, TicketType
from engagement.models import Question, QuestionUpvote
from events.models import Event, Session


class EventFlowTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.event = Event.objects.create(
            name="Test Conf",
            slug="test-conf",
            starts_on=today,
            ends_on=today + timedelta(days=1),
            is_published=True,
        )
        self.ticket = TicketType.objects.create(
            event=self.event, name="Standard", price=Decimal("0.00"), quantity=2
        )
        self.session = Session.objects.create(
            event=self.event,
            title="Opening keynote",
            starts_at=timezone.now() + timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        self.user = User.objects.create_user("attendee", password="pw12345!")

    def _register(self):
        registration = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            full_name="Test Person",
            email="test@example.com",
        )
        AttendeeProfile.objects.create(registration=registration)
        return registration

    def test_agenda_renders_for_anonymous_visitors(self):
        response = self.client.get(reverse("agenda", args=[self.event.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Opening keynote")

    def test_registration_creates_profile_and_badge(self):
        response = self.client.post(
            reverse("register", args=[self.event.slug]),
            {
                "full_name": "New Person",
                "email": "New@Example.com",
                "organization": "Acme",
                "job_title": "Analyst",
                "ticket_type": self.ticket.pk,
                "consent": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        registration = Registration.objects.get(email="new@example.com")
        self.assertEqual(len(registration.badge_code), 8)
        self.assertTrue(registration.profile.is_visible)

    def test_duplicate_email_is_rejected(self):
        self._register()
        response = self.client.post(
            reverse("register", args=[self.event.slug]),
            {
                "full_name": "Someone Else",
                "email": "test@example.com",
                "ticket_type": self.ticket.pk,
            },
        )
        self.assertContains(response, "already registered")

    def test_bookmark_toggles(self):
        registration = self._register()
        self.client.force_login(self.user)
        url = reverse("toggle_bookmark", args=[self.event.slug, self.session.pk])
        self.client.post(url)
        self.assertTrue(
            AgendaItem.objects.filter(
                registration=registration, session=self.session
            ).exists()
        )
        self.client.post(url)
        self.assertFalse(
            AgendaItem.objects.filter(
                registration=registration, session=self.session
            ).exists()
        )

    def test_question_upvote_is_one_per_person(self):
        registration = self._register()
        question = Question.objects.create(
            session=self.session, registration=registration, body="Why?"
        )
        self.client.force_login(self.user)
        url = reverse("upvote_question", args=[self.event.slug, question.pk])
        self.client.post(url)
        self.client.post(url)  # toggles back off
        self.assertEqual(QuestionUpvote.objects.filter(question=question).count(), 0)

    def test_unpublished_event_is_hidden(self):
        self.event.is_published = False
        self.event.save()
        response = self.client.get(reverse("event_home", args=[self.event.slug]))
        self.assertEqual(response.status_code, 404)

    def test_dashboard_requires_organizer(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("organizer_dashboard", args=[self.event.slug])
        )
        self.assertEqual(response.status_code, 403)
