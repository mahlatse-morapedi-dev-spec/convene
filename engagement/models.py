from django.db import models

from attendees.models import Registration
from events.models import Event, Session


class Poll(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="polls")
    question = models.CharField(max_length=300)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return PollVote.objects.filter(option__poll=self).count()


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=200)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return self.text

    @property
    def vote_count(self):
        return self.votes.count()

    def share(self):
        total = self.poll.total_votes
        return round(100 * self.vote_count / total) if total else 0


class PollVote(models.Model):
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="poll_votes"
    )
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("option", "registration")]


class Question(models.Model):
    """Audience Q&A against a session."""

    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="questions"
    )
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="questions"
    )
    body = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.body[:60]

    @property
    def display_name(self):
        return "Anonymous" if self.is_anonymous else self.registration.full_name

    @property
    def upvote_count(self):
        return self.upvotes.count()


class QuestionUpvote(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="upvotes"
    )
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="question_upvotes"
    )

    class Meta:
        unique_together = [("question", "registration")]


class Topic(models.Model):
    """A community board thread — the pre-event conversation surface."""

    RIDESHARE = "rideshare"
    MEETUP = "meetup"
    DISCUSSION = "discussion"
    JOBS = "jobs"
    KINDS = [
        (DISCUSSION, "Discussion"),
        (MEETUP, "Meet-up"),
        (RIDESHARE, "Travel and lifts"),
        (JOBS, "Jobs"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="topics")
    kind = models.CharField(max_length=20, choices=KINDS, default=DISCUSSION)
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="topics"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def reply_count(self):
        return self.posts.count()

    @property
    def last_post(self):
        return self.posts.order_by("-created_at").first()


class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="posts")
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="posts"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.registration.full_name} on {self.topic.title}"


class SessionFeedback(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="feedback"
    )
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE, related_name="session_feedback"
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("session", "registration")]

    def __str__(self):
        return f"{self.rating}/5 — {self.session.title}"
