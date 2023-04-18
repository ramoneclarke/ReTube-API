from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=200)
    stripe_product_id = models.CharField(max_length=100, blank=True)
    snippets_monthly_limit = models.IntegerField()
    snippets_max_length = models.IntegerField(help_text="Maximum length of a video snippet in seconds")
    summaries_monthly_limit = models.IntegerField()
    summaries_max_video_length = models.IntegerField(help_text="Maximum length for a video to summarise in seconds")
    search_max_playlists = models.IntegerField()
    search_max_playlist_videos = models.IntegerField(help_text="Maximum amoount of videos per playlist")
    search_max_video_length = models.IntegerField(help_text="Maximum length for a video in seconds")


class Subscription(models.Model):
    user = models.OneToOneField(User, related_name="subscription", on_delete=models.CASCADE, default=None)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    snippets_usage = models.IntegerField(default=0)
    summaries_usage = models.IntegerField(default=0)
    search_playlists_active = models.IntegerField(default=0)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    interval = models.CharField(max_length=50, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_product_id = models.CharField(max_length=100, blank=True)

