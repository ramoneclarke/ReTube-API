from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import stripe
import environ
import json
import datetime
from models import Subscription, SubscriptionPlan
from serializers import CreateCheckoutSessionSerializer



env = environ.Env()
# reading .env file
environ.Env.read_env()

stripe.api_key = env("STRIPE_API_KEY")

@api_view(['POST'])
def test_payment(request):
    test_payment_intent = stripe.PaymentIntent.create(
        amount=1000, currency='gbp', 
        payment_method_types=['card'],
        receipt_email='test@example.com')
    return Response(status=status.HTTP_200_OK, data=test_payment_intent)

def calculate_order_amount(items):
    # Replace this constant with a calculation of the order's amount
    # Calculate the order total on the server to prevent
    # people from directly manipulating the amount on the client
    return 1400

class CreatePaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = request.data
        try:
            # Create a PaymentIntent with the order amount and currency
            intent = stripe.PaymentIntent.create(
                amount=calculate_order_amount(data['items']),
                currency='gbp',
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            return Response({'clientSecret': intent.client_secret}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)


class CreateCheckoutSessionView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, format=None):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        price_id = serializer.validated_data['price_id']

        try:
            user = request.user
            # checking if customer with email already exists
            customer_data = stripe.Customer.list(email=user.email).data  
            if customer_data:
                customer_id = customer_data[0].id
                session = stripe.checkout.Session.create(
                    success_url='http://127.0.0.1:3000/account?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url='http://127.0.0.1:3000/account/',
                    mode='subscription',
                    line_items=[{
                        'price': price_id,
                        'quantity': 1
                    }],
                    customer=customer_id,
                )
            else:
                session = stripe.checkout.Session.create(
                    success_url='http://127.0.0.1:3000/account?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url='http://127.0.0.1:3000/account/',
                    mode='subscription',
                    line_items=[{
                        'price': price_id,
                        'quantity': 1
                    }],
                    customer_email=user.email,
                )
            return Response({'redirect': session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)



 
class WebhookReceivedView(APIView):
    permission_classes = [AllowAny]
    @csrf_exempt

    def post(self, request, format=None):
        webhook_secret = env("STRIPE_WEBHOOK_SECRET")

        if webhook_secret:
            # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
            sig_header = request.headers.get('STRIPE_SIGNATURE')
            payload = request.body

            try:
                event = stripe.Webhook.construct_event(
                    payload=payload, sig_header=sig_header, secret=webhook_secret)
                data = event['data']
            except Exception as e:
                return Response({'status': 'failure', 'message': str(e)}, status=400)
            # Get the type of webhook event sent - used to check the status of PaymentIntents.
            event_type = event['type']
        else:
            data = request.data['data']
            event_type = request.data['type']
        data_object = data['object']

        if event_type == 'checkout.session.completed':
            # Payment is successful and the subscription is created.
            # You should provision the subscription and save the customer ID to your database.
            print('checkout.session.completed')
            print("DATA OBJECT: ")
            print(data_object)

            subscription_id = data_object.subscription
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            subscription_obj = Subscription.objects.get(user__email=data_object.customer_details.email)
            end_date_unix_timestamp = stripe_subscription.current_period_end
            end_date = datetime.datetime.fromtimestamp(end_date_unix_timestamp).date()

            subscription_obj.stripe_subscription_id = subscription_id
            subscription_obj.stripe_customer_id = stripe_subscription.customer
            subscription_obj.stripe_product_id = stripe_subscription.items.data[0].price.product
            subscription_obj.end_date = end_date
            subscription_obj.interval = stripe_subscription.items.data[0].price.recurring.interval
            plan = SubscriptionPlan.objects.get(stripe_product_id=stripe_subscription.items.data[0].price.product)
            subscription_obj.plan = plan
            subscription_obj.monthly_limit = plan.monthly_limit
            subscription_obj.save()
            


        elif event_type == 'invoice.paid':
            # Continue to provision the subscription as payments continue to be made.
            # Store the status in your database and check when a user accesses your service.
            # This approach helps you avoid hitting rate limits.
            print(data)
        elif event_type == 'invoice.payment_failed':
            # The payment failed or the customer does not have a valid payment method.
            # The subscription becomes past_due. Notify your customer and send them to the
            # customer portal to update their payment information.
            print(data)
        else:
            print('Unhandled event type {}'.format(event_type))

        return Response({'status': 'success'})