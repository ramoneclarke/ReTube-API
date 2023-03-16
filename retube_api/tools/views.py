from django.shortcuts import render
import os
from rest_framework.response import Response
from django.http import HttpResponseBadRequest
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from .models import Snippet, Summary, YoutubeVideo
from tools.serializers import (
    SnippetSerializer,
    YoutubePlaylistSerializer,
    SummarySerializer
)
from tools.utils import create_text_snippet, create_summary
from users.permissions import IsOwner



class VideoSnippetView(APIView):
    """
    Fetch all of the user's snippets or create a new snippet.
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, format=None):
        user = request.user
        snippets = Snippet.objects.filter(owner=user)
        self.check_object_permissions(request,snippets)
        snippet_serializer = SnippetSerializer(snippets, many=True, context={"request": request})
        return Response(snippet_serializer.data)

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


class SummaryView(APIView):
    """
    Fetch a video summary or create a new summary.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        video_id = request.data.get('video_id', None)
        if not video_id:
            return Response({'error': 'video_id is required'}, status=400)
        summary = Summary.objects.filter(video__video_id=video_id)
        summary_serializer = SummarySerializer(summary, context={"request": request})
        return Response(summary_serializer.data)

    def post(self, request, format=None):
        video_id = request.data.get('video_id', None)
        
        if not video_id:
            return Response({'error': 'video_id is required'}, status=400)
        
        # Check if a YoutubeVideo with the same video_id exists, and if it has a summary. If not, generate a summary
        if YoutubeVideo.objects.filter(video_id=video_id).exists():
            video = YoutubeVideo.objects.get(video_id=video_id)
            if Summary.objects.filter(video=video).exists():
                summary = Summary.objects.get(video=video)
            else:
                summary = create_summary(video_id)
        else:
            summary = create_summary(video_id)
        
        if isinstance(summary, HttpResponseBadRequest):
            return summary
        
        serializer = SummarySerializer(summary)

        return Response(serializer.data)




