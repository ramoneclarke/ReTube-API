from rest_framework import serializers
from django.contrib.auth.models import User
from .models import YoutubeVideo, Summary, Snippet, YoutubePlaylist

class YoutubeVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeVideo
        fields = ('id', 'title', 'video_id', 'url')

class SummarySerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer()
    class Meta:
        model = Summary
        fields = ('id', 'summary_text', 'bullet_points', 'video')

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


class UserSerializer(serializers.HyperlinkedModelSerializer):
    snippets = SnippetSerializer(many=True, read_only=True)
    playlists = YoutubePlaylistSerializer(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source="owner.username")

    @staticmethod
    def validate_username(username):
        if "allauth.account" not in settings.INSTALLED_APPS:
            # We don't need to call the all-auth
            # username validator unless its installed
            return username

        from allauth.account.adapter import get_adapter

        username = get_adapter().clean_username(username)
        return username

    class Meta:
        extra_fields = []
        if hasattr(User, "USERNAME_FIELD"):
            extra_fields.append(User.USERNAME_FIELD)
        if hasattr(User, "EMAIL_FIELD"):
            extra_fields.append(User.EMAIL_FIELD)
        model = User
        fields = (
            "id",
            "username",
            "favourites",
            "watchlist",
            "owner",
            *extra_fields,
        )
        depth = 1
        read_only_fields = ("email",)