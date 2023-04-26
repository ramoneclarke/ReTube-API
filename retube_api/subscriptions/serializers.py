from rest_framework import serializers
from .models import Subscription, SubscriptionPlan


class CreateCheckoutSessionSerializer(serializers.Serializer):
    price_id = serializers.CharField()

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'stripe_product_id',
            'snippets_monthly_limit',
            'snippets_max_length',
            'summaries_monthly_limit',
            'summaries_max_video_length',
            'search_max_playlists',
            'search_max_playlist_videos',
            'search_max_video_length',
        ]

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'user',
            'plan',
            'snippets_usage',
            'summaries_usage',
            'search_playlists_active',
            'start_date',
            'end_date',
            'interval',
            'stripe_subscription_id',
            'stripe_customer_id',
            'stripe_product_id',
        ]