from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django_warrant.models import get_user as gu

class APIKeyMiddleware(object):
    """
        A simple middleware to pull the users API key from the headers and
        attach it to the request.

        It should be compatible with both old and new style middleware.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)

        return response

    @staticmethod
    def process_request(request):
        if 'HTTP_AUTHORIZATION_ID' in request.META:
            request.api_key = request.META['HTTP_AUTHORIZATION_ID']

        return None


def get_user(request):
    if not hasattr(request, '_cached_user'):

        request._cached_user = gu(request)

    return request._cached_user


class CognitoAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE%s setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        ) % ("_CLASSES" if settings.MIDDLEWARE is None else "")
        request.user = get_user(request)
