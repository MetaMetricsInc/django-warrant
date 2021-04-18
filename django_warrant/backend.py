"""Custom Django authentication backend"""
import abc

from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils.crypto import salted_hmac
from warrant_lite import WarrantLite

from django_warrant.models import UserObj
from .utils import cognito_to_dict


class AbstractCognitoBackend(ModelBackend):
    __metaclass__ = abc.ABCMeta

    UNAUTHORIZED_ERROR_CODE = 'NotAuthorizedException'

    USER_NOT_FOUND_ERROR_CODE = 'UserNotFoundException'


    @abc.abstractmethod
    def authenticate(self, username=None, password=None):
        """
        Authenticate a Cognito User
        :param username: Cognito username
        :param password: Cognito password
        :return: returns User instance of AUTH_USER_MODEL or None
        """
        wl = WarrantLite(username=username, password=password,
                         pool_id=settings.COGNITO_USER_POOL_ID,
                         client_id=settings.COGNITO_APP_ID,
                         client_secret=settings.COGNITO_CLIENT_SECRET)

        try:
            tokens = wl.authenticate_user()
        except (Boto3Error, ClientError) as e:
            return self.handle_error_response(e)

        access_token = tokens['AuthenticationResult']['AccessToken']
        refresh_token = tokens['AuthenticationResult']['RefreshToken']
        id_token = tokens['AuthenticationResult']['IdToken']
        wl.verify_token(access_token, 'access_token', 'access')
        wl.verify_token(id_token, 'id_token', 'id')

        cognito_user = wl.client.get_user(
            AccessToken=access_token
        )
        user = self.get_user_obj(username,cognito_user)
        if user:
            user.access_token = access_token
            user.id_token = id_token
            user.refresh_token = refresh_token

        return user

    def get_user_obj(self,username,cognito_user):
        user_attrs = cognito_to_dict(cognito_user.get('UserAttributes'),
                                     settings.COGNITO_ATTR_MAPPING or {
            'email':'email',
            'given_name':'first_name',
            'family_name':'last_name'
        })
        User = get_user_model()
        django_fields = [f.name for f in User._meta.get_fields()]
        extra_attrs = {}
        new_user_attrs = user_attrs.copy()

        for k, v in user_attrs.items():
            if k not in django_fields:
                extra_attrs.update({k: new_user_attrs.pop(k, None)})
        user_attrs = new_user_attrs
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            u = None
        if u:
            for k, v in extra_attrs.items():
                setattr(u, k, v)
        return u

    def handle_error_response(self, error):
        error_code = error.response['Error']['Code']
        if error_code in [
                AbstractCognitoBackend.UNAUTHORIZED_ERROR_CODE,
                AbstractCognitoBackend.USER_NOT_FOUND_ERROR_CODE
            ]:
            return None
        raise error


class CognitoBackend(AbstractCognitoBackend):
    def authenticate(self, request, username=None, password=None):
        """
        Authenticate a Cognito User and store an access, ID and
        refresh token in the session.
        """
        user = super(CognitoBackend, self).authenticate(
            username=username, password=password)
        if user:
            request.session['ACCESS_TOKEN'] = user.access_token
            request.session['ID_TOKEN'] = user.id_token
            request.session['REFRESH_TOKEN'] = user.refresh_token
            request.session.save()
        return user


class CognitoNoModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None):
        wl = WarrantLite(username=username, password=password,
                         pool_id=settings.COGNITO_USER_POOL_ID,
                         client_id=settings.COGNITO_APP_ID,
                         client_secret=settings.COGNITO_CLIENT_SECRET)

        try:
            tokens = wl.authenticate_user()
        except (Boto3Error, ClientError) as e:
            return self.handle_error_response(e)

        access_token = tokens['AuthenticationResult']['AccessToken']
        refresh_token = tokens['AuthenticationResult']['RefreshToken']
        id_token = tokens['AuthenticationResult']['IdToken']
        wl.verify_token(access_token, 'access_token', 'access')
        wl.verify_token(id_token, 'id_token', 'id')

        user = UserObj(wl.client.get_user(
            AccessToken=access_token
        ),access_token=access_token,is_authenticated=True)
        user.refresh_token = refresh_token
        user.access_token = access_token
        user.id_token = id_token
        user.session_auth_hash = get_session_auth_hash(password)
        if user:
            request.session['ACCESS_TOKEN'] = user.access_token
            request.session['ID_TOKEN'] = user.id_token
            request.session['REFRESH_TOKEN'] = user.refresh_token
            request.session.save()
        return user

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None

    def get_user(self,user_id):
        pass
    

def get_session_auth_hash(password):
    """
    Return an HMAC of the password field.
    """
    key_salt = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
    return salted_hmac(key_salt, password).hexdigest()