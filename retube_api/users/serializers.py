from rest_framework import serializers
from tools.serializers import SnippetSerializer, YoutubePlaylistSerializer
from .models import CustomUserModel

class CustomUserModelSerializer(serializers.ModelSerializer):
    snippets = SnippetSerializer(many=True, read_only=True)
    playlists = YoutubePlaylistSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUserModel
        fields = [
            "userId",
            "username",
            "email",
            "password",
            "snippets",
            "playlists"
        ]
    def create(self, validated_data):
        user = CustomUserModel.objects.create_user(
            validated_data["username"],
            validated_data["email"],
            validated_data["password"]
        )

        return user
