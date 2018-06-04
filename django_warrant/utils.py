import boto3
from django.conf import settings
from warrant_lite import WarrantLite


apigw_client = boto3.client('apigateway')
cog_client = boto3.client('cognito-idp')


def cognito_to_dict(attr_list,mapping):
    user_attrs = dict()
    for i in attr_list:
        name = mapping.get(i.get('Name'))
        if name:
            value = i.get('Value')
            user_attrs[name] = value
    return user_attrs


def dict_to_cognito(attr_dict,mapping):
    cognito_list = list()
    inv_map = {v: k for k, v in mapping.items()}
    for k,v in attr_dict.items():
        name = inv_map.get(k)
        cognito_list.append({'Name':name,'Value':v})
    return cognito_list


def attr_map_inverse():
    attr_dict = settings.COGNITO_ATTR_MAPPING.copy()
    attr_dict.pop('username')
    attr_dict.pop('phone_number_verified')
    return {v: k for k, v in attr_dict.items()}


def user_obj_to_django(user_obj):
    c_attrs = settings.COGNITO_ATTR_MAPPING
    user_attrs = dict()
    for k,v in user_obj.__dict__.iteritems():
        dk = c_attrs.get(k)
        if dk:
            user_attrs[dk] = v
    return user_attrs


def refresh_access_token(request):
    """
    Sets a new access token on the User using the refresh token.
    """

    refresh_token = request.session['REFRESH_TOKEN']
    auth_params = {'REFRESH_TOKEN': refresh_token}
    if settings.COGNITO_CLIENT_SECRET:
        username = request.user.username
        auth_params['SECRET_HASH'] = WarrantLite.get_secret_hash(username,
                                        settings.COGNITO_APP_ID,
                                        settings.COGNITO_CLIENT_SECRET)
    refresh_response = cog_client.initiate_auth(
        ClientId=settings.COGNITO_APP_ID,
        AuthFlow='REFRESH_TOKEN',
        AuthParameters=auth_params,
    )
    request.session['ACCESS_TOKEN'] = refresh_response['AuthenticationResult']['AccessToken']
    request.session['ID_TOKEN'] = refresh_response['AuthenticationResult']['IdToken']
    request.session.save()
    return {
            'access_token': refresh_response['AuthenticationResult']['AccessToken'],
            'id_token': refresh_response['AuthenticationResult']['IdToken'],
            'token_type': refresh_response['AuthenticationResult']['TokenType']
        }