from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from attendees.forms import CheckInForm, MessageForm, ProfileForm, RegistrationForm
from attendees.models import AttendeeProfile, Message, Registration
from attendees.services import get_registration
from events.models import Event


def register(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    existing = get_registration(request, event)
    if existing:
        messages.info(request, "You're already registered for this event.")
        return redirect("my_ticket", slug=event.slug)

    if request.method == "POST":
        form = RegistrationForm(request.POST, event=event)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            if request.user.is_authenticated:
                registration.user = request.user
            registration.save()
            AttendeeProfile.objects.create(
                registration=registration,
                is_visible=form.cleaned_data["consent"],
            )
            messages.success(
                request, f"You're in. Badge code {registration.badge_code}."
            )
            if request.user.is_authenticated:
                return redirect("my_ticket", slug=event.slug)
            return redirect("event_home", slug=event.slug)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "full_name": request.user.get_full_name(),
                "email": request.user.email,
            }
        form = RegistrationForm(event=event, initial=initial)

    return render(
        request, "attendees/register.html", {"event": event, "form": form}
    )


@login_required
def my_ticket(request, slug):
    event = get_object_or_404(Event, slug=slug)
    registration = get_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)
    return render(
        request,
        "attendees/my_ticket.html",
        {"event": event, "registration": registration},
    )


def directory(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    viewer = get_registration(request, event)
    if not event.allow_public_directory and not viewer:
        return HttpResponseForbidden("The directory is open to registered attendees.")

    people = (
        Registration.objects.filter(event=event, profile__is_visible=True)
        .exclude(status=Registration.CANCELLED)
        .select_related("profile")
    )
    query = request.GET.get("q", "").strip()
    if query:
        people = people.filter(
            Q(full_name__icontains=query)
            | Q(organization__icontains=query)
            | Q(job_title__icontains=query)
            | Q(profile__interests__icontains=query)
        )

    suggested = []
    if viewer and hasattr(viewer, "profile"):
        mine = set(viewer.profile.interest_list())
        if mine:
            for person in people.exclude(pk=viewer.pk)[:200]:
                shared = mine & set(person.profile.interest_list())
                if shared:
                    suggested.append((person, sorted(shared)))
            suggested.sort(key=lambda pair: len(pair[1]), reverse=True)
            suggested = suggested[:6]

    return render(
        request,
        "attendees/directory.html",
        {
            "event": event,
            "people": people.order_by("full_name"),
            "query": query,
            "viewer": viewer,
            "suggested": suggested,
        },
    )


def attendee_detail(request, slug, pk):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    person = get_object_or_404(
        Registration.objects.select_related("profile"), pk=pk, event=event
    )
    if not hasattr(person, "profile") or not person.profile.is_visible:
        return HttpResponseForbidden("This attendee is not listed.")
    viewer = get_registration(request, event)
    shared = []
    if viewer and hasattr(viewer, "profile"):
        shared = viewer.profile.shared_interests_with(person.profile)
    return render(
        request,
        "attendees/attendee_detail.html",
        {
            "event": event,
            "person": person,
            "viewer": viewer,
            "shared": shared,
            "form": MessageForm(),
        },
    )


@login_required
def send_message(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    sender = get_registration(request, event)
    recipient = get_object_or_404(Registration, pk=pk, event=event)
    if not sender:
        return redirect("register", slug=event.slug)
    if sender.pk == recipient.pk:
        messages.error(request, "You can't message yourself.")
        return redirect("directory", slug=event.slug)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient
            message.save()
            messages.success(request, f"Message sent to {recipient.full_name}.")
            return redirect("attendee_detail", slug=event.slug, pk=recipient.pk)
    return redirect("attendee_detail", slug=event.slug, pk=recipient.pk)


@login_required
def inbox(request, slug):
    event = get_object_or_404(Event, slug=slug)
    registration = get_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)
    received = registration.received_messages.select_related("sender").order_by("-sent_at")
    received.filter(read_at__isnull=True).update(read_at=timezone.now())
    return render(
        request,
        "attendees/inbox.html",
        {
            "event": event,
            "registration": registration,
            "received": received,
            "sent": registration.sent_messages.select_related("recipient").order_by(
                "-sent_at"
            ),
        },
    )


@login_required
def edit_profile(request, slug):
    event = get_object_or_404(Event, slug=slug)
    registration = get_registration(request, event)
    if not registration:
        return redirect("register", slug=event.slug)
    profile, _ = AttendeeProfile.objects.get_or_create(registration=registration)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("attendee_detail", slug=event.slug, pk=registration.pk)
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        "attendees/edit_profile.html",
        {"event": event, "form": form, "registration": registration},
    )


@login_required
def check_in(request, slug):
    """Desk check-in: look a person up by badge code or email and stamp them in."""
    event = get_object_or_404(Event, slug=slug)
    if not event.is_organizer(request.user):
        return HttpResponseForbidden("Organizers only.")

    found = None
    form = CheckInForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"].strip()
        found = (
            Registration.objects.filter(event=event)
            .filter(Q(email__iexact=code) | Q(badge_code__iexact=code))
            .first()
        )
        if not found:
            messages.error(request, f"No registration matches “{code}”.")
        elif found.is_checked_in:
            messages.info(
                request, f"{found.full_name} was already checked in."
            )
        else:
            found.checked_in_at = timezone.now()
            found.save(update_fields=["checked_in_at"])
            messages.success(request, f"Checked in {found.full_name}.")
        form = CheckInForm()

    return render(
        request,
        "attendees/check_in.html",
        {
            "event": event,
            "form": form,
            "found": found,
            "checked_in": event.registrations.filter(
                checked_in_at__isnull=False
            ).count(),
            "total": event.registrations.exclude(
                status=Registration.CANCELLED
            ).count(),
        },
    )
