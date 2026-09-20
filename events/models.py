from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Event(models.Model):
    """The root record. Everything else hangs off one event."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120, blank=True)
    starts_on = models.DateField()
    ends_on = models.DateField()
    timezone_name = models.CharField(max_length=64, default="Africa/Johannesburg")
    is_published = models.BooleanField(default=False)
    allow_public_directory = models.BooleanField(
        default=True, help_text="Let registered attendees browse each other."
    )
    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="organized_events", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_on"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("event_home", args=[self.slug])

    @property
    def is_live(self):
        today = timezone.localdate()
        return self.starts_on <= today <= self.ends_on

    def days(self):
        span = (self.ends_on - self.starts_on).days
        return [self.starts_on + timedelta(days=i) for i in range(span + 1)]

    def is_organizer(self, user):
        return user.is_authenticated and (
            user.is_superuser or self.organizers.filter(pk=user.pk).exists()
        )


class Track(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tracks")
    name = models.CharField(max_length=120)
    colour = models.CharField(max_length=7, default="#1F6F5C")

    class Meta:
        ordering = ["name"]
        unique_together = [("event", "name")]

    def __str__(self):
        return self.name


class Speaker(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="speakers")
    full_name = models.CharField(max_length=160)
    job_title = models.CharField(max_length=160, blank=True)
    organization = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    @property
    def byline(self):
        return ", ".join(p for p in [self.job_title, self.organization] if p)


class Session(models.Model):
    KEYNOTE = "keynote"
    TALK = "talk"
    WORKSHOP = "workshop"
    PANEL = "panel"
    BREAK = "break"
    SOCIAL = "social"
    KINDS = [
        (KEYNOTE, "Keynote"),
        (TALK, "Talk"),
        (WORKSHOP, "Workshop"),
        (PANEL, "Panel"),
        (BREAK, "Break"),
        (SOCIAL, "Social"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions"
    )
    title = models.CharField(max_length=250)
    abstract = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=KINDS, default=TALK)
    room = models.CharField(max_length=120, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    stream_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    slides_url = models.URLField(blank=True)
    speakers = models.ManyToManyField(Speaker, blank=True, related_name="sessions")
    qa_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["starts_at", "room"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("session_detail", args=[self.event.slug, self.pk])

    @property
    def day(self):
        return timezone.localtime(self.starts_at).date()

    @property
    def is_on_now(self):
        return self.starts_at <= timezone.now() <= self.ends_at

    @property
    def has_ended(self):
        return timezone.now() > self.ends_at


class Announcement(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="announcements"
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title
