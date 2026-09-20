import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from attendees.models import Registration
from attendees.services import get_registration
from events.models import Event
from exhibitors.forms import LeadForm
from exhibitors.models import Exhibitor, Lead


def exhibitor_list(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    exhibitors = event.exhibitors.all()
    sponsors = [e for e in exhibitors if e.tier != Exhibitor.EXHIBITOR]
    stands = [e for e in exhibitors if e.tier == Exhibitor.EXHIBITOR]
    return render(
        request,
        "exhibitors/exhibitor_list.html",
        {"event": event, "sponsors": sponsors, "stands": stands},
    )


def exhibitor_detail(request, slug, pk):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    exhibitor = get_object_or_404(Exhibitor, pk=pk, event=event)
    viewer = get_registration(request, event)
    is_staff = bool(viewer and exhibitor.staff.filter(pk=viewer.pk).exists())
    return render(
        request,
        "exhibitors/exhibitor_detail.html",
        {
            "event": event,
            "exhibitor": exhibitor,
            "viewer": viewer,
            "is_staff": is_staff,
            "already_shared": bool(
                viewer and exhibitor.leads.filter(registration=viewer).exists()
            ),
        },
    )


@login_required
def share_details(request, slug, pk):
    """Attendee-initiated lead: 'send my details to this stand'."""
    event = get_object_or_404(Event, slug=slug)
    exhibitor = get_object_or_404(Exhibitor, pk=pk, event=event)
    viewer = get_registration(request, event)
    if not viewer:
        return redirect("register", slug=event.slug)

    _, created = Lead.objects.get_or_create(exhibitor=exhibitor, registration=viewer)
    if created:
        messages.success(request, f"Your details went to {exhibitor.name}.")
    else:
        messages.info(request, f"{exhibitor.name} already has your details.")
    return redirect(exhibitor.get_absolute_url())


def _staff_or_403(request, exhibitor):
    viewer = get_registration(request, exhibitor.event)
    if exhibitor.event.is_organizer(request.user):
        return viewer
    if viewer and exhibitor.staff.filter(pk=viewer.pk).exists():
        return viewer
    return None


@login_required
def lead_capture(request, slug, pk):
    """Stand-side scanner stand-in: type a badge code to capture a lead."""
    event = get_object_or_404(Event, slug=slug)
    exhibitor = get_object_or_404(Exhibitor, pk=pk, event=event)
    staff = _staff_or_403(request, exhibitor)
    if staff is None:
        return HttpResponseForbidden("You don't work this stand.")

    form = LeadForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["badge_code"].strip()
        attendee = Registration.objects.filter(
            event=event, badge_code__iexact=code
        ).first()
        if not attendee:
            messages.error(request, f"No badge matches “{code}”.")
        else:
            lead, created = Lead.objects.get_or_create(
                exhibitor=exhibitor,
                registration=attendee,
                defaults={
                    "note": form.cleaned_data["note"],
                    "captured_by": staff,
                },
            )
            if created:
                messages.success(request, f"Captured {attendee.full_name}.")
            else:
                messages.info(request, f"{attendee.full_name} is already a lead.")
        form = LeadForm()

    return render(
        request,
        "exhibitors/lead_capture.html",
        {
            "event": event,
            "exhibitor": exhibitor,
            "form": form,
            "leads": exhibitor.leads.select_related("registration")[:50],
        },
    )


@login_required
def export_leads(request, slug, pk):
    event = get_object_or_404(Event, slug=slug)
    exhibitor = get_object_or_404(Exhibitor, pk=pk, event=event)
    if _staff_or_403(request, exhibitor) is None:
        return HttpResponseForbidden("You don't work this stand.")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{exhibitor.name}-leads.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Organization", "Job title", "Captured", "Note"])
    for lead in exhibitor.leads.select_related("registration"):
        r = lead.registration
        writer.writerow(
            [
                r.full_name,
                r.email,
                r.organization,
                r.job_title,
                lead.captured_at.isoformat(timespec="minutes"),
                lead.note,
            ]
        )
    return response
