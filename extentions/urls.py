from django.urls import path

from .views import ExtentionsHomeView

urlpatterns = [
    path("", ExtentionsHomeView.as_view(), name="extentions-home"),
]
