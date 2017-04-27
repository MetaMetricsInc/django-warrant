# Warrant + Django
 
 This package contains the following.
 
 - [Install](#install)
 - [Django Auth Backend](#django-auth-backend)
 
 - [Auth Backend](#django-auth-backend) `warrant.django.backend.CognitoBackend`
  - [Using the CognitoBackend](#using-the-cognitobackend)
  - [CognitoBackend Behavior](#cognitobackend-behavior)
  - [Customizing CognitoBackend Behavior](#customizing-cognitobackend-behavior)
- [Profile Views](#profile-views)
 - Profile View
 - Update Profile View
 - Password Reset View
 - User Subscriptions View
 - Admin Subscriptions View

- [API Gateway Integration](#api-gateway-integration)
- [API Key Middleware](#api-key-middleware) `warrant.django.middleware.APIKeyMiddleware`
- [Login view](#login-view)
- [Middlware that adds the auth header to the Django Request object](#api-gateway-middleware)
 
 ## Install 
 `pip install django-warrant`
 
 
 ### Django Auth Backend
 #### Using the CognitoBackend
 1. In your Django project settings file, add the dotted path of
 `CognitoBackend` to your list of `AUTHENTICATION_BACKENDS`.
 Keep in mind that Django will attempt to authenticate a user using
 each backend listed, in the order listed until successful.
 
     ```python
     AUTHENTICATION_BACKENDS = [
         'warrant.django.backend.CognitoBackend',
 
     ]
     ```
 2. Set `COGNITO_USER_POOL_ID` and `COGNITO_APP_ID` in your settings file as well.
 Your User Pool ID can be found in the Pool Details tab in the AWS console.
 Your App ID is found in the Apps tab, listed as "App client id".
 
 3. Set `COGNITO_ATTR_MAPPING` in your settings file to a dictionary mapping a
 Cognito attribute name to a Django User attribute name.
 If your Cognito User Pool has any custom attributes, it is automatically
 prefixed with `custom:`. Therefore, you will want to add a mapping to your
 mapping dictionary as such `{'custom:custom_attr': 'custom_attr'}`.
 Defaults to:
     ```python
     {
         'email': 'email',
         'given_name': 'first_name',
         'family_name': 'last_name',
     }
     ```
 4. Optional - Set `COGNITO_CREATE_UNKNOWN_USERS` to `True` or `False`, depending on if
 you wish local Django users to be created upon successful login. If set to `False`,
 only existing local Django users are updated.
 Defaults to `True`.
 
 5. Optional - Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
 to the AWS access keys you would like to use.
 Defaults to `None`, which will use the default credentials in your `~/.aws/credentials` file.
 
 #### CognitoBackend Behavior
 Since the username of a Cognito User can never change,
 this is used by the backend to match a Cognito User with a local Django
 User.
 
 If a Django user is not found, one is created using the attributes
 fetched from Cognito. If an existing Django user is found, their
 attributes are updated.
 
 If the boto3 client comes back with either a `NotAuthorizedException` or
 `UserNotFoundException`, then `None` is returned instead of a User.
 Otherwise, the exception is raised.
 
 Upon successful login, the three identity tokens returned from Cognito
 (ID token, Refresh token, Access token) are stored in the user's request
 session. In Django >= 1.11, this is done directly in the backend class.
 Otherwise, this is done via the `user_logged_in` signal.
 
 Check the django/demo directory for an example app with a login and
 user details page.
 
 #### Customizing CognitoBackend Behavior
 Setting the Django setting `COGNITO_CREATE_UNKNOWN_USERS` to `False` prevents the backend
 from creating a new local Django user and only updates existing users.
 
 If you create your own backend class that inhereits from `CognitoBackend`, you may
 want to also create your own custom `user_logged_in` so that it checks
 for the name of your custom class.
 
 ### API Gateway Integration
 
 #### API Key Middleware
 The `APIKeyMiddleware` checks for a `HTTP_AUTHORIZATION_ID` header
 in the request and attaches it to the request object as `api_key`.
