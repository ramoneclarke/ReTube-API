from django.urls import path
from tools.views import GoogleLogin

urlpatterns = [
    path('google/', GoogleLogin.as_view(), name='google_login')
]
