import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from events.models import Event, Session


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="ZAR")
    quantity = models.PositiveIntegerField(
        null=True, blank=True, help_text="Leave blank for unlimited."
    )
    sales_close_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]
        unique_together = [("event", "name")]

    def __str__(self):
        return f"{self.name} ({self.event.name})"

    @property
    def sold(self):
        return self.registrations.exclude(status=Registration.CANCELLED).count()

    @property
    def remaining(self):
        if self.quantity is None:
            return None
        return max(self.quantity - self.sold, 0)

    @property
    def is_sold_out(self):
        return self.remaining == 0


class Registration(models.Model):
    """One person's ticket for one event. The identity object the rest of the app hangs off."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    STATUSES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
        null=True,
        blank=True,
    )
    ticket_type = models.ForeignKey(
        TicketType, on_delete=models.PROTECT, related_name="registrations"
    )
    full_name = models.CharField(max_length=160)
    email = models.EmailField()
    organization = models.CharField(max_length=160, blank=True)
    job_title = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default=CONFIRMED)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    badge_code = models.CharField(max_length=8, unique=True, editable=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["full_name"]
        unique_together = [("event", "email")]

    def save(self, *args, **kwargs):
        if not self.badge_code:
            self.badge_code = uuid.uuid4().hex[:8].upper()
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} — {self.event.name}"

    def get_absolute_url(self):
        return reverse("attendee_detail", args=[self.event.slug, self.pk])

    @property
    def is_checked_in(self):
        return self.checked_in_at is not None



class AttendeeProfile(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="profile"
    )
    headline = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    interests = models.CharField(
        max_length=300, blank=True, help_text="Comma-separated topics."
    )
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    photo_url = models.URLField(blank=True)
    is_visible = models.BooleanField(
        default=True, help_text="Show me in the attendee directory."
    )
    open_to_meetings = models.BooleanField(default=True)

    def __str__(self):
        return f"Profile of {self.registration.full_name}"

    def interest_list(self):
        return [i.strip() for i in self.interests.split(",") if i.strip()]

    def shared_interests_with(self, other):
        return sorted(set(self.interest_list()) & set(other.interest_list()))


class AgendaItem(models.Model):
    """A session an attendee has added to their personal schedule."""

    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="agenda_items"
    )
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="agenda_items"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("registration", "session")]
        ordering = ["session__starts_at"]

    def __str__(self):
        return f"{self.registration.full_name} → {self.session.title}"


class Message(models.Model):
    sender = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="received_messages"
    )
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sent_at"]

    def __str__(self):
        return f"{self.sender.full_name} → {self.recipient.full_name}"
