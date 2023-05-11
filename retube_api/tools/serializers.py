from rest_framework import serializers
from .models import YoutubeVideo, Summary, Snippet, YoutubePlaylist


class YoutubeVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeVideo
        fields = ("id", "title", "video_id", "url")


class SummarySerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer()
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Summary
        fields = ("id", "bullet_points", "video", "date_created", "owner")


class SnippetSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer()
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Snippet
        fields = ("id", "text", "video", "start", "end", "date_created", "owner")


class YoutubePlaylistSerializer(serializers.ModelSerializer):
    videos = YoutubeVideoSerializer(many=True)
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = YoutubePlaylist
        fields = ("id", "name", "videos", "date_created", "owner")
