from django.db import models
from users.models import CustomUserModel


class YoutubeVideo(models.Model):
    title = models.CharField(max_length=100)
    video_id = models.CharField(max_length=15)
    length = models.IntegerField()
    url = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Summary(models.Model):
    bullet_points = models.TextField()
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        CustomUserModel,
        related_name="summaries",
        on_delete=models.CASCADE,
        default=None,
    )


class Snippet(models.Model):
    text = models.TextField()
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE)
    start = models.CharField(max_length=40, default="00:00:01.00")
    end = models.CharField(max_length=40, default="00:00:02.00")
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        CustomUserModel, related_name="snippets", on_delete=models.CASCADE, default=None
    )

    def __str__(self):
        return self.text


class YoutubePlaylist(models.Model):
    name = models.CharField(max_length=200)
    videos = models.ManyToManyField(YoutubeVideo)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        CustomUserModel,
        related_name="playlists",
        on_delete=models.CASCADE,
        default=None,
    )

    def __str__(self):
        return self.name
