import datetime

from django.conf import settings
from jose import jwt

from django_warrant.utils import cognito_to_dict, dict_to_cognito, cog_client


class UserObj(object):

    def __init__(self, attribute_list, metadata=None, request=None):
        """
        :param attribute_list:
        :param metadata: Dictionary of User metadata
        """

        self._attr_map = settings.COGNITO_ATTR_MAPPING
        self.username = attribute_list.get('Username')
        self._data = cognito_to_dict(
            attribute_list.get('UserAttributes')
            or attribute_list.get('Attributes'),self._attr_map)

        self.sub = self._data.pop('sub',None)
        self.email_verified = self._data.pop('email_verified',None)
        self.phone_number_verified = self._data.pop('phone_number_verified',None)
        self._metadata = {} if metadata is None else metadata
        if request:
            self.access_token = request.session['ACCESS_TOKEN']
            self.refresh_token = request.session['REFRESH_TOKEN']
            self.id_token = request.session['ID_TOKEN']

    def __repr__(self):
        return '<{class_name}: {uni}>'.format(
            class_name=self.__class__.__name__, uni=self.__unicode__())

    def __unicode__(self):
        return self.username

    def __getattr__(self, name):
        if name in list(self.__dict__.get('_data',{}).keys()):
            return self._data.get(name)
        if name in list(self.__dict__.get('_metadata',{}).keys()):
            return self._metadata.get(name)

    def __setattr__(self, name, value):
        if name in list(self.__dict__.get('_data',{}).keys()):
            self._data[name] = value
        else:
            super(UserObj, self).__setattr__(name, value)

    def check_token(self, renew=True):
        """
        Checks the exp attribute of the access_token and either refreshes
        the tokens by calling the renew_access_tokens method or does nothing
        :param renew: bool indicating whether to refresh on expiration
        :return: bool indicating whether access_token has expired
        """
        if not self.access_token:
            raise AttributeError('Access Token Required to Check Token')
        now = datetime.datetime.now()
        dec_access_token = jwt.get_unverified_claims(self.access_token)

        if now > datetime.datetime.fromtimestamp(dec_access_token['exp']):
            expired = True
            if renew:
                self.renew_access_token()
        else:
            expired = False
        return expired

    def renew_access_token(self):
        """
        Sets a new access token on the User using the refresh token.
        """
        auth_params = {'REFRESH_TOKEN': self.refresh_token}
        self._add_secret_hash(auth_params, 'SECRET_HASH')
        refresh_response = cog_client.initiate_auth(
            ClientId=settings.COGNITO_APP_ID,
            AuthFlow='REFRESH_TOKEN',
            AuthParameters=auth_params,
        )

        self.access_token = refresh_response['AuthenticationResult']['AccessToken']
        self.id_token = refresh_response['AuthenticationResult']['IdToken']
        self.token_type = refresh_response['AuthenticationResult']['TokenType']


    def save(self,admin=False,create=False,password=None):
        if not create:
            if admin:
                cog_client.admin_update_user_attributes(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=self.username,
                    UserAttributes=dict_to_cognito(self._data,self._attr_map))
                return
            cog_client.update_user_attributes(
                UserAttributes=dict_to_cognito(self._data, self._attr_map),
                AccessToken=self.access_token
            )
            return
        else:
            cog_client.sign_up(
                ClientId=settings.COGNITO_APP_ID,
                Username=self.username,
                Password=password,
                UserAttributes=dict_to_cognito(self._data, self._attr_map)
            )
            return

    def delete(self,admin=False):
        cog_client.admin_disable_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=self.username
        )
        return
