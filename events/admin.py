from django.contrib import admin

from events.models import Announcement, Event, Session, Speaker, Track


class TrackInline(admin.TabularInline):
    model = Track
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "starts_on", "ends_on", "city", "is_published")
    list_filter = ("is_published",)
    search_fields = ("name", "city")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("organizers",)
    inlines = [TrackInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "track", "starts_at", "room", "kind")
    list_filter = ("event", "track", "kind")
    search_fields = ("title", "abstract")
    filter_horizontal = ("speakers",)
    date_hierarchy = "starts_at"


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "organization", "event")
    list_filter = ("event",)
    search_fields = ("full_name", "organization")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "is_pinned", "created_at")
    list_filter = ("event", "is_pinned")


admin.site.register(Track)
