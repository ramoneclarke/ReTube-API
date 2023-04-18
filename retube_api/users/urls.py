from django.urls import path
from .views import GoogleLogin, UserDataView, get_csrf

urlpatterns = [
    path('social/login/google/', GoogleLogin.as_view(), name='google_login'),
    path('user_data', UserDataView.as_view(), name='user-data'),
    path("csrf/", get_csrf, name="api-csrf"),
]
