from django.urls import path

from exhibitors import views

urlpatterns = [
    path("e/<slug:slug>/exhibitors/", views.exhibitor_list, name="exhibitor_list"),
    path(
        "e/<slug:slug>/exhibitors/<int:pk>/",
        views.exhibitor_detail,
        name="exhibitor_detail",
    ),
    path(
        "e/<slug:slug>/exhibitors/<int:pk>/share/",
        views.share_details,
        name="share_details",
    ),
    path(
        "e/<slug:slug>/exhibitors/<int:pk>/leads/",
        views.lead_capture,
        name="lead_capture",
    ),
    path(
        "e/<slug:slug>/exhibitors/<int:pk>/leads.csv",
        views.export_leads,
        name="export_leads",
    ),
]
