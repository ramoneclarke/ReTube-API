from django.shortcuts import render
import os
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from .models import Snippet
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

    permission_classes = [IsAuthenticated, IsOwner]

    def post(self, request, format=None):
        user = request.user
        video_id = request.data.get('video_id', None)
        start = request.data.get('start', None)
        end = request.data.get('end', None)
        
        if not video_id:
            return Response({'error': 'video_id is required'}, status=400)
        if not start:
            return Response({'error': 'start is required'}, status=400)
        if not end:
            return Response({'error': 'end is required'}, status=400)
        
        # Check if a Snippet with the same video id, start, and end already exists for the given user
        if Snippet.objects.filter(owner=user, video__video_id=video_id, start=start, end=end).exists():
            return Response({'detail': 'Snippet with the same video_id, start, and end already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        snippet = create_text_snippet(video_id, start, end, request.user)
        serializer = SnippetSerializer(snippet)

        return Response(serializer.data)




