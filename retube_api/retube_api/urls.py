from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from subscriptions.views import PlansView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("accounts/", include("allauth.urls")),
    path("tools/", include("tools.urls")),
    path("api/", include("users.urls")),
    path("payments/", include("subscriptions.urls")),
    path("plans/", PlansView.as_view(), name="plans"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
