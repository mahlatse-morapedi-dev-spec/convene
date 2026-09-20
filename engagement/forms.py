from django import forms

from engagement.models import Post, Question, SessionFeedback, Topic


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["body", "is_anonymous"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Ask the speaker something."}
            )
        }
        labels = {"body": "Your question", "is_anonymous": "Ask anonymously"}


class TopicForm(forms.ModelForm):
    first_post = forms.CharField(
        label="Opening post", widget=forms.Textarea(attrs={"rows": 4})
    )

    class Meta:
        model = Topic
        fields = ["kind", "title"]


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}
        labels = {"body": "Reply"}


class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f"{i}") for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Rate this session",
    )

    class Meta:
        model = SessionFeedback
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Anything the organizers should know?"}
            )
        }
