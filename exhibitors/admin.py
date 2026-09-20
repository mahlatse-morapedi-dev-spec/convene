from django.contrib import admin

from exhibitors.models import Exhibitor, Lead


@admin.register(Exhibitor)
class ExhibitorAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "tier", "booth_number", "lead_count")
    list_filter = ("event", "tier")
    search_fields = ("name",)
    filter_horizontal = ("staff",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("registration", "exhibitor", "captured_at")
    list_filter = ("exhibitor__event", "exhibitor")
