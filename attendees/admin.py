from django.contrib import admin

from attendees.models import AgendaItem, AttendeeProfile, Message, Registration, TicketType


class ProfileInline(admin.StackedInline):
    model = AttendeeProfile
    extra = 0


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "event",
        "ticket_type",
        "status",
        "badge_code",
        "checked_in_at",
    )
    list_filter = ("event", "status", "ticket_type")
    search_fields = ("full_name", "email", "organization", "badge_code")
    inlines = [ProfileInline]
    readonly_fields = ("badge_code", "reference")


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "price", "quantity", "sold", "is_active")
    list_filter = ("event", "is_active")


admin.site.register([AgendaItem, Message])
