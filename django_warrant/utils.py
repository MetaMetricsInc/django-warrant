import boto3
from django.conf import settings


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

def user_obj_to_django(user_obj):
    c_attrs = settings.COGNITO_ATTR_MAPPING
    user_attrs = dict()
    for k,v in user_obj.__dict__.iteritems():
        dk = c_attrs.get(k)
        if dk:
            user_attrs[dk] = v
    return user_attrs


