from django.urls import path

from . import views

app_name = "links"

urlpatterns = [
    path("lucky/", views.lucky, name="lucky"),
    path("", views.lucky, name="lucky"),
    path("lucky/fortune/", views.fortune_status, name="fortune_status"),
    # path("", views.landing, name="landing"),
    path("<slug:slug>/links/", views.profile_links, name="profile_links"),
    path("<slug:slug>/go/<int:link_id>/", views.track_link, name="link_redirect"),
    path("<slug:slug>/", views.landing, name="profile"),
]
