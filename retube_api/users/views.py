from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.middleware.csrf import get_token
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from users.serializers import CustomUserModelSerializer
from users.models import CustomUserModel
from users.serializers import CustomSocialLoginSerializer

@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "snippets": reverse("snippets", request=request, format=format),
            "playlists": reverse("playlists", request=request, format=format),
        }
    )

def get_csrf(request):
    token = get_token(request)
    print("CSRF TOKEN: ", token)
    response = JsonResponse({"Result": "Success - Set CSRF cookie", "X-CSRFToken": token})
    return response

class UserList(generics.ListAPIView):
    queryset = CustomUserModel.objects.all()
    serializer_class = CustomUserModelSerializer

    permission_classes = [permissions.IsAdminUser]


class CustomSocialLoginView(SocialLoginView):
    serializer_class = CustomSocialLoginSerializer

class GoogleLogin(CustomSocialLoginView):
    authentication_classes = []
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:3000'
    client_class = OAuth2Client
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
