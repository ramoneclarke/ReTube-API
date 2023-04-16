from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.csrf import csrf_exempt
import stripe
import environ
import json
import datetime
from .models import Subscription, SubscriptionPlan
from .serializers import CreateCheckoutSessionSerializer, SubscriptionSerializer



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
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
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


class CreateCustomerPortalSessionView(APIView):
    def post(self, request, format=None):
        try:
            user = request.user
            # checking if customer with email already exists
            customer_data = stripe.Customer.list(email=user.email).data
            print(f"customer_data: {customer_data}")
            customer_id = customer_data[0].id
            # Authenticate your user.
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url='http://127.0.0.1:3000/account/',
            )
            return Response({'redirect': session.url}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


 
class WebhookReceivedView(APIView):
    permission_classes = [AllowAny]
    @csrf_exempt

    def post(self, request, format=None):
        webhook_secret = env("STRIPE_WEBHOOK_SECRET")

        if webhook_secret:
            # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
            sig_header = request.META['HTTP_STRIPE_SIGNATURE']
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
            plan = SubscriptionPlan.objects.get(stripe_product_id=stripe_subscription.plan.product)
            start_date_unix_timestamp = stripe_subscription.current_period_start
            start_date = datetime.datetime.fromtimestamp(start_date_unix_timestamp).date()
            end_date_unix_timestamp = stripe_subscription.current_period_end
            end_date = datetime.datetime.fromtimestamp(end_date_unix_timestamp).date()

            serializer = SubscriptionSerializer(subscription_obj, data={
                'stripe_subscription_id': subscription_id,
                'stripe_customer_id': stripe_subscription.customer,
                'stripe_product_id': stripe_subscription.plan.product,
                'start_date': start_date,
                'end_date': end_date,
                'interval': stripe_subscription.plan.interval,
                'plan': plan.id,
                'snippets_usage': 0,
                'summaries_usage': 0,
                'search_playlists_active': subscription_obj.search_playlists_active,
            })

            if serializer.is_valid():
                serializer.save()
            else:
                print(serializer.errors)


        elif event_type == 'invoice.paid':
            # Continue to provision the subscription as payments continue to be made.
            # Store the status in your database and check when a user accesses your service.
            # This approach helps you avoid hitting rate limits.
            subscription_id = data_object.subscription
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            subscription_obj = Subscription.objects.get(user__email=data_object.customer_email)
            
            previous_plan = subscription_obj.plan
            plan = SubscriptionPlan.objects.get(stripe_product_id=stripe_subscription.plan.product)

            if plan == previous_plan:
                # subscription renewal
                start_date_unix_timestamp = stripe_subscription.current_period_start
                start_date = datetime.datetime.fromtimestamp(start_date_unix_timestamp).date()
                end_date_unix_timestamp = stripe_subscription.current_period_end
                end_date = datetime.datetime.fromtimestamp(end_date_unix_timestamp).date()

                serializer = SubscriptionSerializer(subscription_obj, data={
                    'snippets_usage': 0,
                    'summaries_usage': 0,
                })

                if serializer.is_valid():
                    serializer.save()
                else:
                    print(serializer.errors)
            else:
                # new subscription. subscription created in 'checkout.session.completed' event
                pass

        elif event_type == 'customer.subscription.deleted':
            # Sent when a customer’s subscription ends.
            subscription_obj = Subscription.objects.get(stripe_customer_id=data_object.customer)
            free_plan = SubscriptionPlan.objects.get(name='free')

            serializer = SubscriptionSerializer(subscription_obj, data={
                'stripe_subscription_id': '',
                'stripe_customer_id': data_object.customer,
                'stripe_product_id': '',
                'start_date': datetime.datetime.now(),
                'end_date': None,
                'interval': '',
                'plan': free_plan.id,
                'search_playlists_active': subscription_obj.search_playlists_active,
            })

            if serializer.is_valid():
                serializer.save()
            else:
                print(serializer.errors)

        elif event_type == 'customer.subscription.updated':
            # Listen to this to monitor subscription upgrades and downgrades.
            print("DATA OBJECT:")
            print(data_object)
            subscription_id = data_object.id
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            subscription_obj = Subscription.objects.get(stripe_customer_id=data_object.customer)
            
            previous_plan = subscription_obj.plan
            if previous_plan.name != 'free':
                plan = SubscriptionPlan.objects.get(stripe_product_id=stripe_subscription.plan.product)
                start_date_unix_timestamp = stripe_subscription.current_period_start
                start_date = datetime.datetime.fromtimestamp(start_date_unix_timestamp).date()
                end_date_unix_timestamp = stripe_subscription.current_period_end
                end_date = datetime.datetime.fromtimestamp(end_date_unix_timestamp).date()

                serializer = SubscriptionSerializer(subscription_obj, data={
                    'stripe_product_id': stripe_subscription.plan.product,
                    'start_date': start_date,
                    'end_date': end_date,
                    'interval': stripe_subscription.plan.interval,
                    'plan': plan.id,
                })

                if serializer.is_valid():
                    serializer.save()
                else:
                    print(serializer.errors)
        else:
            print('Unhandled event type {}'.format(event_type))

        return Response({'status': 'success'})
