from django.contrib import admin

from engagement.models import (
    Poll,
    PollOption,
    PollVote,
    Post,
    Question,
    QuestionUpvote,
    SessionFeedback,
    Topic,
)


class OptionInline(admin.TabularInline):
    model = PollOption
    extra = 3


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "session", "is_open", "total_votes")
    list_filter = ("is_open", "session__event")
    inlines = [OptionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("body", "session", "display_name", "upvote_count", "is_answered")
    list_filter = ("session__event", "is_answered", "is_hidden")
    actions = ["mark_answered"]

    @admin.action(description="Mark selected questions as answered")
    def mark_answered(self, request, queryset):
        queryset.update(is_answered=True)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "kind", "reply_count", "created_at")
    list_filter = ("event", "kind", "is_locked")


admin.site.register([PollOption, PollVote, Post, QuestionUpvote, SessionFeedback])
