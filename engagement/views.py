from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from attendees.services import get_registration
from engagement.forms import FeedbackForm, PostForm, QuestionForm, TopicForm
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
from events.models import Event, Session


def _require_registration(request, event):
    registration = get_registration(request, event)
    if not registration:
        messages.error(request, "Register for this event to join in.")
    return registration


@login_required
def ask_question(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    session = get_object_or_404(Session, pk=pk, event=event)
    registration = _require_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)
    if not session.qa_enabled:
        messages.error(request, "Q&A is closed for this session.")
        return redirect(session.get_absolute_url())

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.session = session
            question.registration = registration
            question.save()
            messages.success(request, "Question posted.")
    return redirect(session.get_absolute_url() + "#qa")


@login_required
def upvote_question(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    question = get_object_or_404(Question, pk=pk, session__event=event)
    registration = _require_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)

    vote = QuestionUpvote.objects.filter(
        question=question, registration=registration
    ).first()
    if vote:
        vote.delete()
    else:
        QuestionUpvote.objects.create(question=question, registration=registration)
    return redirect(question.session.get_absolute_url() + "#qa")


@login_required
def vote_poll(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    poll = get_object_or_404(Poll, pk=pk, session__event=event)
    registration = _require_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)
    if not poll.is_open:
        messages.error(request, "That poll has closed.")
        return redirect(poll.session.get_absolute_url())

    option_id = request.POST.get("option")
    option = get_object_or_404(PollOption, pk=option_id, poll=poll)
    PollVote.objects.filter(option__poll=poll, registration=registration).delete()
    PollVote.objects.create(option=option, registration=registration)
    messages.success(request, "Vote counted.")
    return redirect(poll.session.get_absolute_url() + "#polls")


@login_required
def leave_feedback(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    session = get_object_or_404(Session, pk=pk, event=event)
    registration = _require_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)

    instance = SessionFeedback.objects.filter(
        session=session, registration=registration
    ).first()
    form = FeedbackForm(request.POST, instance=instance)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.session = session
        feedback.registration = registration
        feedback.save()
        messages.success(request, "Thanks — feedback recorded.")
    else:
        messages.error(request, "Pick a rating between 1 and 5.")
    return redirect(session.get_absolute_url() + "#feedback")


def board(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    topics = (
        event.topics.select_related("created_by")
        .annotate(replies=Count("posts"))
        .order_by("-created_at")
    )
    kind = request.GET.get("kind")
    if kind:
        topics = topics.filter(kind=kind)
    return render(
        request,
        "engagement/board.html",
        {
            "event": event,
            "topics": topics,
            "kinds": Topic.KINDS,
            "active_kind": kind,
            "registration": get_registration(request, event),
        },
    )


def topic_detail(request, slug, pk):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    topic = get_object_or_404(
        Topic.objects.select_related("created_by"), pk=pk, event=event
    )
    return render(
        request,
        "engagement/topic_detail.html",
        {
            "event": event,
            "topic": topic,
            "posts": topic.posts.select_related("registration"),
            "form": PostForm(),
            "registration": get_registration(request, event),
        },
    )


@login_required
def new_topic(request, slug):
    event = get_object_or_404(Event, slug=slug)
    registration = _require_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)

    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.event = event
            topic.created_by = registration
            topic.save()
            Post.objects.create(
                topic=topic,
                registration=registration,
                body=form.cleaned_data["first_post"],
            )
            return redirect("topic_detail", slug=event.slug, pk=topic.pk)
    else:
        form = TopicForm()
    return render(
        request, "engagement/new_topic.html", {"event": event, "form": form}
    )


@login_required
def reply(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    topic = get_object_or_404(Topic, pk=pk, event=event)
    registration = _require_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)
    if topic.is_locked:
        messages.error(request, "This thread is locked.")
        return redirect("topic_detail", slug=event.slug, pk=topic.pk)

    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.topic = topic
        post.registration = registration
        post.save()
    return redirect("topic_detail", slug=event.slug, pk=topic.pk)
