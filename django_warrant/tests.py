from __future__ import unicode_literals

from mock import patch, MagicMock
from botocore.exceptions import ClientError
from importlib import import_module
from unittest import skipIf

from django import VERSION as DJANGO_VERSION
from django.contrib.auth.models import AnonymousUser, User
from django.conf import settings
from django.contrib.auth import get_user_model, signals, authenticate as django_authenticate
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test import override_settings, TestCase, TransactionTestCase
from django.test.client import RequestFactory
from django.utils.six import iteritems

from django_warrant.backend import CognitoBackend
from django_warrant.middleware import APIKeyMiddleware


def set_tokens(cls, *args, **kwargs):
    cls.access_token = 'accesstoken'
    cls.id_token = 'idtoken'
    cls.refresh_token = 'refreshtoken'

def authenticate_user(cls,*args, **kwargs):
    return {
        'ChallengeParameters': {},
        'AuthenticationResult': {
            'AccessToken': 'fake.access.token',
            'ExpiresIn': 3600,
            'TokenType': 'Bearer',
            'RefreshToken': 'fake.refresh.token',
            'IdToken': 'fake.id.token'},
        'ResponseMetadata': {
            'RequestId': 'abc123-1234-4567-789-9101112',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {
                'date': 'Thu, 10 May 2018 15:23:12 GMT',
                'content-type': 'application/x-amz-json-1.1',
                'content-length': '4056',
                'connection': 'keep-alive',
                'x-amzn-requestid': 'abc123-f233-sfsdf-k342334'},
            'RetryAttempts': 0}
        }

def verify_tokens(cls,*args, **kwargs):
    return {
        'sub': 'asfadfadf-3323sd-sdt4-adf22-5dfgdfsaddf',
        'event_id': 'sdf44sdsd-3234-9540-8a21-234sdfdsff',
        'token_use': 'access',
        'scope': 'aws.cognito.signin.user.admin',
        'auth_time': 1525966559,
        'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Bgbf9cyLt',
        'exp': 1525970159,
        'iat': 1525966559,
        'jti': '23ssdfsdf-tt44-5678-9fgv-345dfgdfgfdfgg',
        'client_id': '7dsfsdfdsfdfgkdfkkd',
        'username': 'fakeusername'
    }

def get_user(cls, *args, **kwargs):
    user = {
        'user_status': kwargs.pop('user_status', 'CONFIRMED'),
        'username': kwargs.pop('access_token', 'testuser'),
        'email': kwargs.pop('email', 'test@email.com'),
        'given_name': kwargs.pop('given_name', 'FirstName'),
        'family_name': kwargs.pop('family_name', 'LastName'),
        'UserAttributes': 
        [
            {
                "Name": "sub", 
                "Value": "c7d890f6-eb38-498d-8f85-7a6c4af33d7a"
            }, 
            {
                "Name": "email_verified", 
                "Value": "true"
            }, 
            {
                "Name": "gender", 
                "Value": "male"
            }, 
            {
                "Name": "name", 
                "Value": "FirstName LastName"
            }, 
            {
                "Name": "preferred_username", 
                "Value": "testuser"
            }, 
            {
                "Name": "given_name", 
                "Value": "FirstName"
            }, 
            {
                "Name": "family_name", 
                "Value": "LastName"
            }, 
            {
                "Name": "email", 
                "Value": "test@email.com"
            },
            {
                "Name": "custom:api_key",
                "Value": "abcdefg"
            },
            {
                "Name": "custom:api_key_id",
                "Value": "ab-1234"
            }
        ]
    }
    user_metadata = {
        'username': user.get('Username'),
        'id_token': cls.id_token,
        'access_token': cls.access_token,
        'refresh_token': cls.refresh_token,
        'api_key': user.get('custom:api_key', None),
        'api_key_id': user.get('custom:api_key_id', None)
    }

    return cls.get_user_obj(username=cls.username,
                             attribute_list=user.get('UserAttributes'),
                             metadata=user_metadata)


def create_request():
    request = HttpRequest()
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session.save()
    request.session = session

    return request


def authenticate(username, password):
    if DJANGO_VERSION[1] > 10:
        request = create_request()
        return django_authenticate(request=request, username=username, password=password)
    else:
        return django_authenticate(username=username, password=password)


def login(client, username, password):
    if DJANGO_VERSION[1] > 10:
        request = create_request()
        return client.login(request=request, username=username, password=password)
    else:
        return client.login(username=username, password=password)


class AuthTests(TransactionTestCase):
    @patch.object(Cognito, 'authenticate')
    @patch.object(Cognito, 'get_user')
    def test_user_authentication(self, mock_get_user, mock_authenticate):
        Cognito.authenticate = set_tokens
        Cognito.get_user = get_user
        user = authenticate(username='testuser',
                            password='password')

        self.assertIsNotNone(user)

    @patch.object(Cognito, 'authenticate')
    def test_user_authentication_wrong_password(self, mock_authenticate):
        Cognito.authenticate.side_effect = ClientError(
            {
                'Error': 
                    {
                        'Message': 'Incorrect username or password.', 'Code': 'NotAuthorizedException'
                    }
            },
            'AdminInitiateAuth')
        user = authenticate(username='username',
                            password='wrongpassword')

        self.assertIsNone(user)


    @patch.object(Cognito, 'authenticate')
    def test_user_authentication_wrong_username(self, mock_authenticate):
        Cognito.authenticate.side_effect = ClientError(
            {
                'Error': 
                    {
                        'Message': 'Incorrect username or password.', 'Code': 'NotAuthorizedException'
                    }
            },
            'AdminInitiateAuth')
        user = authenticate(username='wrongusername',
                            password='password')

        self.assertIsNone(user)

    @patch.object(Cognito, 'authenticate')
    @patch.object(Cognito, 'get_user')
    def test_client_login(self, mock_get_user, mock_authenticate):
        Cognito.authenticate = set_tokens
        Cognito.get_user = get_user
        user = login(self.client, username='testuser',
                                 password='password')
        self.assertTrue(user)

    @patch.object(Cognito, 'authenticate')
    def test_boto_error_raised(self, mock_authenticate):
        """
        Check that any error other than NotAuthorizedException is
        raised as an exception
        """
        Cognito.authenticate.side_effect = ClientError(
            {
                'Error': 
                    {
                        'Message': 'Generic Error Message.', 'Code': 'SomeError'
                    }
            },
            'AdminInitiateAuth')
        with self.assertRaises(ClientError) as error:
            user = authenticate(username='testuser',
                                password='password')
        self.assertEqual(error.exception.response['Error']['Code'], 'SomeError')

    @patch.object(Cognito, 'authenticate')
    @patch.object(Cognito, 'get_user')
    def test_new_user_created(self, mock_get_user, mock_authenticate):
        Cognito.authenticate = set_tokens
        Cognito.get_user = get_user

        User = get_user_model()
        self.assertEqual(User.objects.count(), 0) 
        user = authenticate(username='testuser',
                            password='password')

        self.assertEqual(User.objects.count(), 1) 
        self.assertEqual(user.username, 'testuser')

    @patch.object(Cognito, 'authenticate')
    @patch.object(Cognito, 'get_user')
    def test_existing_user_updated(self, mock_get_user, mock_authenticate):
        Cognito.authenticate = set_tokens
        Cognito.get_user = get_user

        User = get_user_model()
        existing_user = User.objects.create(username='testuser', email='None')
        user = authenticate(username='testuser',
                            password='password')
        self.assertEqual(user.id, existing_user.id)
        self.assertNotEqual(user.email, existing_user.email)
        self.assertEqual(User.objects.count(), 1)

        updated_user = User.objects.get(username='testuser')
        self.assertEqual(updated_user.email, user.email)
        self.assertEqual(updated_user.id, user.id)

    @override_settings(COGNITO_CREATE_UNKNOWN_USERS=False)
    @patch.object(Cognito, 'authenticate')
    @patch.object(Cognito, 'get_user') 
    def test_existing_user_updated_disabled_create_unknown_user(self, mock_get_user, mock_authenticate):
        Cognito.authenticate = set_tokens
        Cognito.get_user = get_user

        User = get_user_model()
        existing_user = User.objects.create(username='testuser', email='None')

        user = authenticate(username='testuser',
                            password='password')
        self.assertEqual(user.id, existing_user.id)
        self.assertNotEqual(user.email, existing_user)
        self.assertEqual(User.objects.count(), 1)

        updated_user = User.objects.get(username='testuser')
        self.assertEqual(updated_user.email, user.email)
        self.assertEqual(updated_user.id, user.id)

    @override_settings(COGNITO_CREATE_UNKNOWN_USERS=False)
    @patch.object(Cognito, 'authenticate')
    @patch.object(Cognito, 'get_user') 
    def test_user_not_found_disabled_create_unknown_user(self, mock_get_user, mock_authenticate):
        Cognito.authenticate = set_tokens
        Cognito.get_user = get_user

        user = authenticate(username='testuser',
                            password='password')

        self.assertIsNone(user)

    @skipIf(DJANGO_VERSION[1] > 10, "Signal not used if Django>1.10")
    def test_add_user_tokens_signal(self):
        User = get_user_model()
        user = User.objects.create(username=settings.COGNITO_TEST_USERNAME)
        user.access_token = 'access_token_value'
        user.id_token = 'id_token_value'
        user.refresh_token = 'refresh_token_value'
        user.backend = 'warrant.django.backend.CognitoBackend'
        user.api_key = 'abcdefg'
        user.api_key_id = 'ab-1234'

        request = RequestFactory().get('/login')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        signals.user_logged_in.send(sender=user.__class__, request=request, user=user)

        self.assertEqual(request.session['ACCESS_TOKEN'], 'access_token_value')
        self.assertEqual(request.session['ID_TOKEN'], 'id_token_value')
        self.assertEqual(request.session['REFRESH_TOKEN'], 'refresh_token_value')
        self.assertEqual(request.session['API_KEY'], 'abcdefg')
        self.assertEqual(request.session['API_KEY_ID'], 'ab-1234')

    def test_model_backend(self):
        """
        Check that the logged in signal plays nice with other backends
        """
        User = get_user_model()
        user = User.objects.create(username=settings.COGNITO_TEST_USERNAME)
        user.backend = 'django.contrib.auth.backends.ModelBackend'

        request = RequestFactory().get('/login')
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        signals.user_logged_in.send(sender=user.__class__, request=request, user=user)
        

class MiddleWareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_header_missing(self):
        request = self.factory.get('/does/not/matter')

        request.user = AnonymousUser()

        APIKeyMiddleware.process_request(request)

        # Test that missing headers responds properly
        self.assertFalse(hasattr(request, 'api_key'))

    def test_header_transfers(self):
        request = self.factory.get('/does/not/matter', HTTP_AUTHORIZATION_ID='testapikey')

        request.user = AnonymousUser()

        APIKeyMiddleware.process_request(request)

        # Now test with proper headers in place
        self.assertEqual(request.api_key, 'testapikey')
