from django.urls import path

from attendees import views

urlpatterns = [
    path("e/<slug:slug>/register/", views.register, name="register"),
    path("e/<slug:slug>/ticket/", views.my_ticket, name="my_ticket"),
    path("e/<slug:slug>/people/", views.directory, name="directory"),
    path("e/<slug:slug>/people/<int:pk>/", views.attendee_detail, name="attendee_detail"),
    path("e/<slug:slug>/people/<int:pk>/message/", views.send_message, name="send_message"),
    path("e/<slug:slug>/inbox/", views.inbox, name="inbox"),
    path("e/<slug:slug>/profile/", views.edit_profile, name="edit_profile"),
    path("e/<slug:slug>/manage/check-in/", views.check_in, name="check_in"),
]
