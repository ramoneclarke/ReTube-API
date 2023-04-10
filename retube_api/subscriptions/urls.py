from django.urls import path
from subscriptions import views

urlpatterns = [
    path('test-payment/', views.test_payment, name='test-payment'),
    path('create-payment-intent/', views.CreatePaymentView.as_view(), name='create-payment-intent'),
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhooks/', views.WebhookReceivedView.as_view(), name='webhooks')
]