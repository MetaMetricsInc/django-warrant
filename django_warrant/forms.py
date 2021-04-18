from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=200,required=True)
    last_name = forms.CharField(max_length=200,required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=30,required=True,help_text='ex. +14325551212')
    gender = forms.ChoiceField(choices=(('female','Female'),('male','Male')),required=True)
    address = forms.CharField(max_length=200,required=True)
    preferred_username = forms.CharField(max_length=200,required=True)


class AdminProfileForm(ProfileForm):
    api_key = forms.CharField(max_length=200, required=False)
    api_key_id = forms.CharField(max_length=200, required=False)


class APIKeySubscriptionForm(forms.Form):
    plan = forms.ChoiceField(required=True)

    def __init__(self, plans=[], users_plans=[], *args, **kwargs):
        self.base_fields['plan'].choices = [(p.get('id'),p.get('name')) for p in plans if not p.get('id') in users_plans]
        super(APIKeySubscriptionForm, self).__init__(*args, **kwargs)


class ForgotPasswordForm(forms.Form):
    username = forms.CharField(max_length=200,required=True)


class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, required=True, max_length=200)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, max_length=200)

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise ValidationError(_('The passwords entered do not match.'))
        return confirm_password


class VerificationCodeForm(forms.Form):
    username = forms.CharField(max_length=200,required=True)
    verification_code = forms.CharField(max_length=6)


class ConfirmForgotPasswordForm(VerificationCodeForm,PasswordForm):
    pass


class RegistrationForm(ProfileForm,PasswordForm,ForgotPasswordForm):
    pass


class UpdatePasswordForm(PasswordForm):
    previous_password = forms.CharField(max_length=200,
                                        widget=forms.PasswordInput,
                                        required=True)