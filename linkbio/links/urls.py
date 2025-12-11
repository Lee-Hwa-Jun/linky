from django.urls import path

from . import views

app_name = "links"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("<slug:slug>/", views.landing, name="profile"),
]
