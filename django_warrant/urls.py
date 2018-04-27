
from django.contrib.auth import views as auth_views
from django.urls import re_path

from .views import ProfileView,UpdateProfileView,MySubsriptions,\
    AdminListUsers,AdminSubscriptions,LogoutView

app_name = 'dw'

urlpatterns = (
    re_path(r'^login/$', auth_views.login, {'template_name': 'warrant/login.html'}, name='login'),
    re_path(r'^logout/$', LogoutView.as_view(), {'template_name': 'warrant/logout.html'}, name='logout'),
    re_path(r'^profile/$', ProfileView.as_view(),name='profile'),
    re_path(r'^profile/update/$', UpdateProfileView.as_view(),name='update-profile'),
    re_path(r'^profile/subscriptions/$', MySubsriptions.as_view(),name='subscriptions'),
    re_path(r'^admin/cognito-users/$', AdminListUsers.as_view(),name='admin-cognito-users'),
    re_path(r'^admin/cognito-users/(?P<username>[-\w]+)$', AdminSubscriptions.as_view(),name='admin-cognito-user')
)