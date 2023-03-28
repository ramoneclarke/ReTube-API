from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from users.serializers import CustomUserModelSerializer
from users.models import CustomUserModel

@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "users": reverse("user-list", request=request, format=format),
            "snippets": reverse("snippets", request=request, format=format),
            "playlists": reverse("playlists", request=request, format=format),
        }
    )

class UserList(generics.ListAPIView):
    queryset = CustomUserModel.objects.all()
    serializer_class = CustomUserModelSerializer

    permission_classes = [permissions.IsAdminUser]


# class GoogleLogin(SocialLoginView):
#     authentication_classes = []
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = 'http://localhost:3000'
#     client_class = OAuth2Client