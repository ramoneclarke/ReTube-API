from rest_framework import serializers


class CreateCheckoutSessionSerializer(serializers.Serializer):
    price_id = serializers.CharField()

class SubscriptionPlanSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    stripe_product_id = serializers.CharField(max_length=100)

class SubscriptionSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    stripe_subscription_id = serializers.CharField(max_length=100)
    stripe_customer_id = serializers.CharField(max_length=100)
    stripe_product_id = serializers.CharField(max_length=100)
    end_date = serializers.DateField()
    interval = serializers.CharField(max_length=100)
    plan = SubscriptionPlanSerializer()
    monthly_limit = serializers.IntegerField()