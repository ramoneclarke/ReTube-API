from django.urls import path
from .views import GoogleLogin, get_csrf

urlpatterns = [
    path('social/login/google/', GoogleLogin.as_view(), name='google_login'),
    path("csrf/", get_csrf, name="api-csrf"),
]
