from django.db import models
from users.models import CustomUserModel


class YoutubeVideo(models.Model):
    title = models.CharField(max_length=100)
    video_id = models.CharField(max_length=15)
    url = models.CharField(max_length=200)
    def __str__(self):
        return self.title   

class Summary(models.Model):
    summary_text = models.CharField(max_length=4000)
    bullet_points = models.CharField(max_length=4000)
    video = models.OneToOneField(YoutubeVideo, on_delete=models.CASCADE)    


class Snippet(models.Model):
    text = models.CharField(max_length=100)
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE)
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
        CustomUserModel, related_name="playlists", on_delete=models.CASCADE, default=None
    )

    def __str__(self):
        return self.name 