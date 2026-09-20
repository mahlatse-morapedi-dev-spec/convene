from django.db import models
from django.urls import reverse

from attendees.models import Registration
from events.models import Event


class Exhibitor(models.Model):
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    EXHIBITOR = "exhibitor"
    TIERS = [
        (PLATINUM, "Platinum sponsor"),
        (GOLD, "Gold sponsor"),
        (SILVER, "Silver sponsor"),
        (EXHIBITOR, "Exhibitor"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="exhibitors")
    name = models.CharField(max_length=160)
    tier = models.CharField(max_length=20, choices=TIERS, default=EXHIBITOR)
    blurb = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    booth_number = models.CharField(max_length=20, blank=True)
    staff = models.ManyToManyField(
        Registration, blank=True, related_name="exhibitor_roles"
    )

    class Meta:
        ordering = ["tier", "name"]
        unique_together = [("event", "name")]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("exhibitor_detail", args=[self.event.slug, self.pk])

    @property
    def lead_count(self):
        return self.leads.count()


class Lead(models.Model):
    """A scanned or opted-in attendee contact, owned by the exhibitor."""

    exhibitor = models.ForeignKey(
        Exhibitor, on_delete=models.CASCADE, related_name="leads"
    )
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="leads"
    )
    note = models.TextField(blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)
    captured_by = models.ForeignKey(
        Registration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="captured_leads",
    )

    class Meta:
        unique_together = [("exhibitor", "registration")]
        ordering = ["-captured_at"]

    def __str__(self):
        return f"{self.registration.full_name} → {self.exhibitor.name}"
