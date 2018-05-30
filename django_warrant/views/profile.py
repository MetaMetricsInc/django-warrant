from botocore.exceptions import ClientError

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache

from django_warrant.utils import cog_client
from django_warrant.views.mixins import GetUserMixin, TokenMixin

try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.contrib.auth.views import LogoutView as DJLogoutView


from django_warrant.forms import ProfileForm, ForgotPasswordForm, ConfirmForgotPasswordForm


class ProfileView(LoginRequiredMixin,TokenMixin,GetUserMixin,TemplateView):
    template_name = 'warrant/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['user'] = self.get_user()
        return context


class UpdateProfileView(LoginRequiredMixin,TokenMixin,GetUserMixin,FormView):
    template_name = 'warrant/update-profile.html'
    form_class = ProfileForm

    def get_success_url(self):
        return reverse_lazy('dw:profile')

    def get_initial(self):
        self.user = self.get_user()
        return self.user._data
    
    def form_valid(self, form):
        if not self.user:
            self.user = self.get_user()
        self.user._data = form.cleaned_data
        self.user.save()
        messages.success(self.request,_('You have successfully updated your profile.'))
        return super(UpdateProfileView, self).form_valid(form)


class LogoutView(DJLogoutView):

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        request.session.delete()
        return super(LogoutView, self).dispatch(request, *args, **kwargs)


class ForgotPasswordView(FormView):
    template_name = 'warrant/forgot-password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('dw:confirm-forgot-password')

    def form_valid(self, form):
        try:
            resp = cog_client.forgot_password(
                ClientId=settings.COGNITO_APP_ID,
                Username=form.cleaned_data['username']
            )['CodeDeliveryDetails']

            messages.success(self.request,
                _('Confirmation code delivered to {} by {}'.format(
                    resp['Destination'],resp['DeliveryMedium'])))
            return super(ForgotPasswordView, self).form_valid(form)
        except ClientError:
            form.add_error('username',_('That user does not exist'))
            return self.form_invalid(form)


class ConfirmForgotPasswordView(FormView):
    template_name = 'warrant/confirm-forgot-password.html'
    form_class = ConfirmForgotPasswordForm
    success_url = reverse_lazy('dw:profile')

    def form_valid(self, form):
        try:
            resp = cog_client.confirm_forgot_password(
                ClientId=settings.COGNITO_APP_ID,
                Username=form.cleaned_data['username'],
                ConfirmationCode=form.cleaned_data['verification_code'],
                Password=form.cleaned_data['password']
            )
            if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
                messages.error(self.request,
                    _('We could not verify either your verification code or username'))
            else:
                messages.success(self.request,
                    _('You have successfully changed your password.'))
            return super(ConfirmForgotPasswordView, self).form_valid(form)
        except ClientError as e:

            form.add_error('verification_code',e.response['Error']['Message'])
            return self.form_invalid(form)