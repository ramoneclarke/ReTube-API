from django.contrib import admin
from django.urls import path, include
from tools.views import VideoSnippetView

urlpatterns = [
    path('text-snippet/', VideoSnippetView.as_view(), name='text-snippet')
]
