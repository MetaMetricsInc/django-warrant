from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from django_warrant.views.mixins import GetSubscriptionsMixin


class SubscriptionsView(LoginRequiredMixin,GetSubscriptionsMixin,ListView):
    template_name = 'warrant/subscriptions.html'

    def get_queryset(self):
        return self.get_user_subscriptions()