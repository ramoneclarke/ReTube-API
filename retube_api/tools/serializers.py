from rest_framework import serializers
from .models import YoutubeVideo, Summary, Snippet, YoutubePlaylist
from users.models import CustomUserModel
from django.conf import settings

class YoutubeVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeVideo
        fields = ('id', 'title', 'video_id', 'url')

class SummarySerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer()
    class Meta:
        model = Summary
        fields = ('id', 'bullet_points', 'video')

class SnippetSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer()
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Snippet
        fields = ('id', 'text', 'video', 'date_created', 'owner')

class YoutubePlaylistSerializer(serializers.ModelSerializer):
    videos = YoutubeVideoSerializer(many=True)
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = YoutubePlaylist
        fields = ('id', 'name', 'videos', 'date_created', 'owner')

