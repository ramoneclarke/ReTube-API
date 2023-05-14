from django.contrib import admin
from django.urls import path, include
from tools.views import VideoSnippetView, SummaryView

urlpatterns = [
    path("text-snippet/", VideoSnippetView.as_view(), name="text-snippet"),
    path("video-summary/", SummaryView.as_view(), name="video-summary"),
]
