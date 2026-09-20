from django import forms

from exhibitors.models import Lead


class LeadForm(forms.ModelForm):
    badge_code = forms.CharField(
        label="Attendee badge code",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
    )

    class Meta:
        model = Lead
        fields = ["note"]
        widgets = {
            "note": forms.Textarea(
                attrs={"rows": 2, "placeholder": "What did you talk about?"}
            )
        }
