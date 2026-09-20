from django import forms

from attendees.models import AttendeeProfile, Message, Registration


class RegistrationForm(forms.ModelForm):
    consent = forms.BooleanField(
        label="Show me in the attendee directory",
        required=False,
        initial=True,
    )

    class Meta:
        model = Registration
        fields = ["full_name", "email", "organization", "job_title", "ticket_type"]
        widgets = {"ticket_type": forms.RadioSelect}

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.fields["ticket_type"].queryset = event.ticket_types.filter(is_active=True)
        self.fields["ticket_type"].empty_label = None

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Registration.objects.filter(event=self.event, email=email).exists():
            raise forms.ValidationError(
                "That email address is already registered for this event."
            )
        return email

    def clean_ticket_type(self):
        ticket = self.cleaned_data["ticket_type"]
        if ticket.is_sold_out:
            raise forms.ValidationError("That ticket is sold out. Pick another.")
        return ticket


class ProfileForm(forms.ModelForm):
    class Meta:
        model = AttendeeProfile
        fields = [
            "headline",
            "bio",
            "interests",
            "linkedin_url",
            "website_url",
            "photo_url",
            "is_visible",
            "open_to_meetings",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "interests": forms.TextInput(
                attrs={"placeholder": "machine learning, public health, policy"}
            ),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Say hello and suggest a time to meet."}
            )
        }
        labels = {"body": "Message"}


class CheckInForm(forms.Form):
    code = forms.CharField(
        label="Badge code or email",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
    )
