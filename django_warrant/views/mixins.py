from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, \
    UserPassesTestMixin, AccessMixin

from django_warrant.models import UserObj
from django_warrant.utils import cog_client, apigw_client


class AdminMixin(LoginRequiredMixin,UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_staff


class GetUserMixin(object):

    def get_user(self):
        return UserObj(cog_client.get_user(
            AccessToken=self.request.session['ACCESS_TOKEN']),
            request=self.request)

    def admin_get_user(self,username):
        return UserObj(cog_client.admin_get_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=username))


class TokenMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('REFRESH_TOKEN'):
            return self.handle_no_permission()
        return super(TokenMixin, self).dispatch(
            request, *args, **kwargs)


class GetSubscriptionsMixin(GetUserMixin):

    def get_subscriptions(self,api_key_id):
        return apigw_client.get_usage_plans(
            keyId=api_key_id).get('items', [])

    def get_user_subscriptions(self):
        return self.get_subscriptions(self.get_user().api_key_id)

    def get_admin_subscriptions(self):
        return self.get_subscriptions(self.admin_get_user(
            self.kwargs.get('username')).api_key_id)