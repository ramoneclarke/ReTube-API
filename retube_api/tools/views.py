from django.shortcuts import render
import os
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from tools.serializers import (
    SnippetSerializer,
    YoutubePlaylistSerializer,
)
from tools.utils import create_text_snippet
from users.permissions import IsOwner



class VideoSnippetView(APIView):
    """
    Fetch all of the user's snippets or create a new snippet.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def post(self, request, format=None):
        video_id = request.data.get('video_id', None)
        if not video_id:
            return Response({'error': 'video_id is required'}, status=400)
        start = request.data.get('start', None)
        if not start:
            return Response({'error': 'start is required'}, status=400)
        end = request.data.get('end', None)
        if not end:
            return Response({'error': 'end is required'}, status=400)
        
        snippet = create_text_snippet(video_id, start, end, request.user)
        serializer = SnippetSerializer(snippet)

        return Response(serializer.data)




