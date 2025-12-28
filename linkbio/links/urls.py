from django.urls import path

from . import views

app_name = "links"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("<slug:slug>/links/", views.profile_links, name="profile_links"),
    path("<slug:slug>/go/<int:link_id>/", views.track_link, name="link_redirect"),
    path("<slug:slug>/", views.landing, name="profile"),
]
