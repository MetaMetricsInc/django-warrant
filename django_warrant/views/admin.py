from django.contrib import messages
from django.views.generic import FormView, TemplateView

from django_warrant.forms import AdminProfileForm
from django_warrant.utils import cog_client

try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy
from django.views.generic.list import ListView

from django.conf import settings
from ..models import UserObj
from .mixins import AdminMixin, GetUserMixin


class AdminListUsers(AdminMixin,ListView):
    template_name = 'warrant/admin-list-users.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        ul = cog_client.list_users(UserPoolId=settings.COGNITO_USER_POOL_ID).get('Users')
        response = [UserObj(i) for i in ul]
        return response


class AdminProfileView(AdminMixin,GetUserMixin,TemplateView):
    template_name = 'warrant/admin-profile.html'

    def get_context_data(self, **kwargs):
        context = super(AdminProfileView, self).get_context_data(**kwargs)
        context['user'] = self.admin_get_user(self.kwargs.get('username'))
        return context


class AdminUpdateProfileView(AdminMixin,GetUserMixin,FormView):
    template_name = 'warrant/admin-update-profile.html'
    form_class = AdminProfileForm

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy('dw:admin-cognito-users')

    def get_initial(self):
        self.user = self.admin_get_user(
            self.kwargs.get('username'))
        return self.user._data

    def form_valid(self, form):
        if not self.user:
            self.user = self.admin_get_user(
                self.kwargs.get('username'))
        self.user._data = form.cleaned_data
        self.user.save(admin=True)
        messages.success(self.request,
            "You have successfully updated {}'s profile.".format(
                self.kwargs.get('username')))
        return super(AdminUpdateProfileView, self).form_valid(form)