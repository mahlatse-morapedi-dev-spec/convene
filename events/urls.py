from django.urls import path

from events import views

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("e/<slug:slug>/", views.event_home, name="event_home"),
    path("e/<slug:slug>/agenda/", views.agenda, name="agenda"),
    path("e/<slug:slug>/agenda/mine/", views.my_schedule, name="my_schedule"),
    path("e/<slug:slug>/sessions/<int:pk>/", views.session_detail, name="session_detail"),
    path(
        "e/<slug:slug>/sessions/<int:pk>/save/",
        views.toggle_bookmark,
        name="toggle_bookmark",
    ),
    path("e/<slug:slug>/speakers/", views.speaker_list, name="speaker_list"),
    path("e/<slug:slug>/speakers/<int:pk>/", views.speaker_detail, name="speaker_detail"),
    path("e/<slug:slug>/manage/", views.organizer_dashboard, name="organizer_dashboard"),
]
