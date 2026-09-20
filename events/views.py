from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from attendees.models import AgendaItem, Registration
from attendees.services import get_registration
from engagement.forms import FeedbackForm, QuestionForm
from engagement.models import Poll, PollVote, Question, QuestionUpvote, SessionFeedback
from events.models import Event, Session, Speaker


def event_list(request):
    events = Event.objects.filter(is_published=True)
    return render(request, "events/event_list.html", {"events": events})


def _event_or_404(slug, request):
    event = get_object_or_404(Event, slug=slug)
    if not event.is_published and not event.is_organizer(request.user):
        raise Http404
    return event


def event_home(request, slug):
    event = _event_or_404(slug, request)
    registration = get_registration(request, event)
    now = timezone.now()
    context = {
        "event": event,
        "registration": registration,
        "announcements": event.announcements.all()[:5],
        "happening_now": event.sessions.filter(
            starts_at__lte=now, ends_at__gte=now
        ).select_related("track")[:4],
        "up_next": event.sessions.filter(starts_at__gt=now).select_related("track")[:4],
        "sponsors": event.exhibitors.exclude(tier="exhibitor")[:8],
        "attendee_count": event.registrations.exclude(
            status=Registration.CANCELLED
        ).count(),
    }
    return render(request, "events/event_home.html", context)


def agenda(request, slug):
    event = _event_or_404(slug, request)
    registration = get_registration(request, event)

    sessions = (
        event.sessions.select_related("track")
        .prefetch_related("speakers")
        .order_by("starts_at")
    )
    track_id = request.GET.get("track")
    if track_id:
        sessions = sessions.filter(track_id=track_id)
    query = request.GET.get("q", "").strip()
    if query:
        sessions = sessions.filter(title__icontains=query)

    bookmarked = set()
    if registration:
        bookmarked = set(
            AgendaItem.objects.filter(registration=registration).values_list(
                "session_id", flat=True
            )
        )

    by_day = defaultdict(list)
    for session in sessions:
        by_day[timezone.localtime(session.starts_at).date()].append(session)

    return render(
        request,
        "events/agenda.html",
        {
            "event": event,
            "registration": registration,
            "days": sorted(by_day.items()),
            "tracks": event.tracks.all(),
            "active_track": track_id,
            "query": query,
            "bookmarked": bookmarked,
        },
    )


def session_detail(request, slug, pk):
    event = _event_or_404(slug, request)
    session = get_object_or_404(
        Session.objects.select_related("track", "event").prefetch_related("speakers"),
        pk=pk,
        event=event,
    )
    registration = get_registration(request, event)

    questions = (
        session.questions.filter(is_hidden=False)
        .select_related("registration")
        .annotate(votes=Count("upvotes"))
        .order_by("-votes", "-created_at")
    )
    my_upvotes = set()
    my_votes = set()
    my_feedback = None
    if registration:
        my_upvotes = set(
            QuestionUpvote.objects.filter(
                registration=registration, question__session=session
            ).values_list("question_id", flat=True)
        )
        my_votes = set(
            PollVote.objects.filter(
                registration=registration, option__poll__session=session
            ).values_list("option__poll_id", flat=True)
        )
        my_feedback = SessionFeedback.objects.filter(
            session=session, registration=registration
        ).first()

    is_bookmarked = bool(
        registration
        and AgendaItem.objects.filter(
            registration=registration, session=session
        ).exists()
    )

    return render(
        request,
        "events/session_detail.html",
        {
            "event": event,
            "session": session,
            "registration": registration,
            "questions": questions,
            "question_form": QuestionForm(),
            "feedback_form": FeedbackForm(instance=my_feedback),
            "my_feedback": my_feedback,
            "polls": session.polls.prefetch_related("options"),
            "my_upvotes": my_upvotes,
            "my_poll_votes": my_votes,
            "is_bookmarked": is_bookmarked,
            "average_rating": session.feedback.aggregate(a=Avg("rating"))["a"],
        },
    )


def speaker_list(request, slug):
    event = _event_or_404(slug, request)
    speakers = event.speakers.prefetch_related("sessions")
    return render(
        request, "events/speaker_list.html", {"event": event, "speakers": speakers}
    )


def speaker_detail(request, slug, pk):
    event = _event_or_404(slug, request)
    speaker = get_object_or_404(Speaker, pk=pk, event=event)
    return render(
        request, "events/speaker_detail.html", {"event": event, "speaker": speaker}
    )


@login_required
def toggle_bookmark(request, slug, pk):
    event = _event_or_404(slug, request)
    session = get_object_or_404(Session, pk=pk, event=event)
    registration = get_registration(request, event)
    if not registration:
        messages.error(request, "Register for this event to build a personal schedule.")
        return redirect(session.get_absolute_url())

    item = AgendaItem.objects.filter(registration=registration, session=session).first()
    if item:
        item.delete()
        messages.success(request, f"Removed “{session.title}” from your schedule.")
    else:
        AgendaItem.objects.create(registration=registration, session=session)
        messages.success(request, f"Added “{session.title}” to your schedule.")
    return redirect(request.POST.get("next") or session.get_absolute_url())


@login_required
def my_schedule(request, slug):
    event = _event_or_404(slug, request)
    registration = get_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)

    items = (
        AgendaItem.objects.filter(registration=registration)
        .select_related("session", "session__track")
        .order_by("session__starts_at")
    )
    by_day = defaultdict(list)
    for item in items:
        by_day[timezone.localtime(item.session.starts_at).date()].append(item.session)

    clashes = set()
    ordered = [i.session for i in items]
    for a, b in zip(ordered, ordered[1:]):
        if a.ends_at > b.starts_at:
            clashes.update({a.pk, b.pk})

    return render(
        request,
        "events/my_schedule.html",
        {
            "event": event,
            "registration": registration,
            "days": sorted(by_day.items()),
            "clashes": clashes,
        },
    )


@login_required
def organizer_dashboard(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not event.is_organizer(request.user):
        return HttpResponseForbidden("You don't organize this event.")

    registrations = event.registrations.exclude(status=Registration.CANCELLED)
    sessions = event.sessions.annotate(
        saves=Count("agenda_items", distinct=True),
        questions_asked=Count("questions", distinct=True),
        rating=Avg("feedback__rating"),
    ).order_by("-saves")

    return render(
        request,
        "organizer/dashboard.html",
        {
            "event": event,
            "registration_count": registrations.count(),
            "checked_in_count": registrations.filter(
                checked_in_at__isnull=False
            ).count(),
            "ticket_types": event.ticket_types.all(),
            "top_sessions": sessions[:10],
            "question_count": Question.objects.filter(session__event=event).count(),
            "post_count": sum(t.reply_count for t in event.topics.all()),
            "lead_count": sum(e.lead_count for e in event.exhibitors.all()),
            "recent_registrations": registrations.order_by("-created_at")[:10],
        },
    )
