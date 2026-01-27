from django.urls import path

from . import views

app_name = "links"

urlpatterns = [
    path("lucky/", views.lucky, name="lucky"),
    path("lucky/fortune/", views.fortune_status, name="fortune_status"),
    path("lucky/fortune/share-token/", views.fortune_share_token, name="fortune_share_token"),
    path("lucky/fortune/share-status/", views.fortune_share_status, name="fortune_share_status"),
    path("lucky/fortune/share-callback/", views.fortune_share_callback, name="fortune_share_callback"),
    path("", views.landing, name="landing"),
    path("<slug:slug>/links/", views.profile_links, name="profile_links"),
    path("<slug:slug>/go/<int:link_id>/", views.track_link, name="link_redirect"),
    path("<slug:slug>/", views.landing, name="profile"),
]
