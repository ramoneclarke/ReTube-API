from rest_framework import serializers
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from tools.serializers import SnippetSerializer, YoutubePlaylistSerializer
from subscriptions.models import SubscriptionPlan, Subscription
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


from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from requests.exceptions import HTTPError

try:
    from allauth.account import app_settings as allauth_account_settings
    from allauth.socialaccount.helpers import complete_social_login
except ImportError:
    raise ImportError('allauth needs to be added to INSTALLED_APPS.')

class CustomSocialLoginSerializer(SocialLoginSerializer):
    def validate(self, attrs):
        view = self.context.get('view')
        request = self._get_request()
        if not view:
            raise serializers.ValidationError(
                _('View is not defined, pass it as a context variable'),
            )
        adapter_class = getattr(view, 'adapter_class', None)
        if not adapter_class:
            raise serializers.ValidationError(_('Define adapter_class in view'))
        adapter = adapter_class(request)
        app = adapter.get_provider().get_app(request)
        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token
        access_token = attrs.get('access_token')
        code = attrs.get('code')
        # Case 1: We received the access_token
        if access_token:
            tokens_to_parse = {'access_token': access_token}
            token = access_token
            # For sign in with apple
            id_token = attrs.get('id_token')
            if id_token:
                tokens_to_parse['id_token'] = id_token
        # Case 2: We received the authorization code
        elif code:
            self.set_callback_url(view=view, adapter_class=adapter_class)
            self.client_class = getattr(view, 'client_class', None)
            if not self.client_class:
                raise serializers.ValidationError(
                    _('Define client_class in view'),
                )
            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope,
                scope_delimiter=adapter.scope_delimiter,
                headers=adapter.headers,
                basic_auth=adapter.basic_auth,
            )
            try:
                token = client.get_access_token(code)
            except OAuth2Error as ex:
                raise serializers.ValidationError(
                    _('Failed to exchange code for access token')
                ) from ex
            access_token = token['access_token']
            tokens_to_parse = {'access_token': access_token}
            # If available we add additional data to the dictionary
            for key in ['refresh_token', 'id_token', adapter.expires_in_key]:
                if key in token:
                    tokens_to_parse[key] = token[key]
        else:
            raise serializers.ValidationError(
                _('Incorrect input. access_token or code is required.'),
            )
        social_token = adapter.parse_token(tokens_to_parse)
        social_token.app = app

        try:
            if adapter.provider_id == 'google' and not code:
                print("Google and not code. id_token: ", id_token)
                login = self.get_social_login(adapter, app, social_token, response={'id_token': id_token})
            else:
                login = self.get_social_login(adapter, app, social_token, token)
            ret = complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_('Incorrect value'))
        if isinstance(ret, HttpResponseBadRequest):
            raise serializers.ValidationError(ret.content)
        if not login.is_existing:
            # We have an account already signed up in a different flow
            # with the same email address: raise an exception.
            # This needs to be handled in the frontend. We can not just
            # link up the accounts due to security constraints
            if allauth_account_settings.UNIQUE_EMAIL:
                # Do we have an account already with this email address?
                account_exists = get_user_model().objects.filter(
                    email=login.user.email,
                ).exists()
                if account_exists:
                    raise serializers.ValidationError(
                        _('User is already registered with this e-mail address.'),
                    )
            login.lookup()
            login.save(request, connect=True)
            print("About to call post signup")
            self.post_signup(login, attrs)
            print("After post signup")
        else:
            print("login is existing. inside else block")
        attrs['user'] = login.account.user
        return attrs

    def post_signup(self, login, attrs):
        """
        Inject behavior when the user signs up with a social account.
        :param login: The social login instance being registered.
        :type login: allauth.socialaccount.models.SocialLogin
        :param attrs: The attributes of the serializer.
        :type attrs: dict
        """
        print(f'login: {login}')
        # Create a new subscription object for the user
        try:
            plan = SubscriptionPlan.objects.get(name="free")
            Subscription.objects.create(user=login.user, plan=plan, snippets_usage=0, 
                                        summaries_usage=0, search_playlists_active=0, 
            )
        except SubscriptionPlan.DoesNotExist:
            print("SubscriptionPlan with name 'free' does not exist")
        except Exception as e:
            print(f"Error creating subscription object: {e}")