from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=200)
    stripe_product_id = models.CharField(max_length=100, blank=True)
    monthly_limit = models.IntegerField()

class Subscription(models.Model):
    user = models.ForeignKey(User, related_name="subscriptions", on_delete=models.CASCADE, default=None)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    monthly_limit = models.IntegerField()
    monthly_usage = models.IntegerField(default=0)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    interval = models.CharField(max_length=50)
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_product_id = models.CharField(max_length=100, blank=True)

