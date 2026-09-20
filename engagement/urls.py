from django.urls import path

from engagement import views

urlpatterns = [
    path("e/<slug:slug>/sessions/<int:pk>/ask/", views.ask_question, name="ask_question"),
    path(
        "e/<slug:slug>/questions/<int:pk>/upvote/",
        views.upvote_question,
        name="upvote_question",
    ),
    path("e/<slug:slug>/polls/<int:pk>/vote/", views.vote_poll, name="vote_poll"),
    path(
        "e/<slug:slug>/sessions/<int:pk>/feedback/",
        views.leave_feedback,
        name="leave_feedback",
    ),
    path("e/<slug:slug>/board/", views.board, name="board"),
    path("e/<slug:slug>/board/new/", views.new_topic, name="new_topic"),
    path("e/<slug:slug>/board/<int:pk>/", views.topic_detail, name="topic_detail"),
    path("e/<slug:slug>/board/<int:pk>/reply/", views.reply, name="reply"),
]
