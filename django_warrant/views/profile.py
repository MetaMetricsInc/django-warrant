from botocore.exceptions import ClientError

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache

from django_warrant.utils import cog_client, dict_to_cognito, apigw_client
from django_warrant.views.mixins import GetUserMixin, TokenMixin

try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.contrib.auth.views import LogoutView as DJLogoutView


from django_warrant.forms import ProfileForm, ForgotPasswordForm, ConfirmForgotPasswordForm, RegistrationForm, \
    VerificationCodeForm, UpdatePasswordForm


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


class CognitoFormView(FormView):
    success_message = None
    client_error_field = None

    def get_success_message(self,resp):
        return self.success_message

    def cognito_command(self,form):
        return {}

    def extra_command(self,form):
        pass

    def form_valid(self, form):
        try:
            resp = self.cognito_command(form)
            self.extra_command(form)
            messages.success(self.request,_(self.get_success_message(resp)))
            return super(CognitoFormView, self).form_valid(form)
        except ClientError as e:
            form.add_error(self.client_error_field, e.response['Error']['Message'])
            return self.form_invalid(form)


class ForgotPasswordView(CognitoFormView):
    template_name = 'warrant/forgot-password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('dw:confirm-forgot-password')
    success_message = 'Confirmation code delivered to {} by {}'
    client_error_field = 'username'

    def cognito_command(self,form):
        return cog_client.forgot_password(
            ClientId=settings.COGNITO_APP_ID,
            Username=form.cleaned_data['username']
        )

    def get_success_message(self,resp):
        return _(self.success_message.format(
            resp['CodeDeliveryDetails']['Destination'],
            resp['CodeDeliveryDetails']['DeliveryMedium']
        ))


class ConfirmForgotPasswordView(CognitoFormView):
    template_name = 'warrant/confirm-forgot-password.html'
    form_class = ConfirmForgotPasswordForm
    success_url = reverse_lazy('dw:profile')
    success_message = 'You have successfully changed your password.'

    def cognito_command(self,form):
        return cog_client.confirm_forgot_password(
            ClientId=settings.COGNITO_APP_ID,
            Username=form.cleaned_data['username'],
            ConfirmationCode=form.cleaned_data['verification_code'],
            Password=form.cleaned_data['password']
        )


class RegistrationView(CognitoFormView):
    template_name = 'warrant/registration.html'
    form_class = RegistrationForm
    success_message = 'Confirmation code delivered to {} by {}'
    success_url = reverse_lazy('dw:confirm-register')
    def get_success_message(self,resp):
        return _(self.success_message.format(
            resp['CodeDeliveryDetails']['Destination'],
            resp['CodeDeliveryDetails']['DeliveryMedium']
        ))

    def cognito_command(self,form):
        cv = form.cleaned_data.copy()
        cv.pop('confirm_password')
        cv['name'] = '{} {}'.format(cv['first_name'],cv['last_name'])
        return cog_client.sign_up(
            ClientId=settings.COGNITO_APP_ID,
            Username=cv.pop('username'),
            Password=cv.pop('password'),
            UserAttributes=dict_to_cognito(cv,
                settings.COGNITO_ATTR_MAPPING)
        )


class ConfirmRegistrationView(GetUserMixin,CognitoFormView):
    template_name = 'warrant/registration.html'
    form_class = VerificationCodeForm
    success_message = 'You have successfully registered.'
    success_url = reverse_lazy('dw:profile')

    def cognito_command(self,form):
        return cog_client.confirm_sign_up(
            ClientId=settings.COGNITO_APP_ID,
            Username=form.cleaned_data['username'],
            ConfirmationCode=form.cleaned_data['verification_code']
        )

    def extra_command(self,form):
        username = form.cleaned_data['username']
        resp = apigw_client.create_api_key(
            name=username,
            description='Created by during registration by django-warrant'
        )
        u = self.admin_get_user(username)
        u.api_key = resp['value']
        u.api_key_id = resp['id']
        u.save(admin=True)


class UpdatePasswordView(LoginRequiredMixin,TokenMixin,CognitoFormView):
    template_name = 'warrant/update-profile.html'
    form_class = UpdatePasswordForm
    success_message = 'You have successfully changed your password.'
    success_url = reverse_lazy('dw:profile')

    def cognito_command(self,form):
        return cog_client.change_password(
            PreviousPassword=form.cleaned_data['previous_password'],
            ProposedPassword=form.cleaned_data['proposed_password'],
            AccessToken=self.request.session['ACCESS_TOKEN']
        )