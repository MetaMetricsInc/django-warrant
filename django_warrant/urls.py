
from django.contrib.auth import views as auth_views
from django.urls import re_path

from django_warrant.views import SubscriptionsView, AdminProfileView
from .views import ProfileView,UpdateProfileView,\
    AdminListUsers,LogoutView,AdminUpdateProfileView

app_name = 'dw'

urlpatterns = (
    re_path(r'^login/$', auth_views.login, {'template_name': 'warrant/login.html'}, name='login'),
    re_path(r'^logout/$', LogoutView.as_view(), {'template_name': 'warrant/logout.html'}, name='logout'),
    re_path(r'^profile/$', ProfileView.as_view(),name='profile'),
    re_path(r'^subscriptions/$', SubscriptionsView.as_view(),name='subscriptions'),
    re_path(r'^profile/update/$', UpdateProfileView.as_view(),name='update-profile'),
    re_path(r'^admin/cognito-users/$', AdminListUsers.as_view(),name='admin-cognito-users'),
    re_path(r'^admin/cognito-users/(?P<username>[-\w]+)/$', AdminProfileView.as_view(),name='admin-cognito-user'),
    re_path(r'^admin/cognito-users/(?P<username>[-\w]+)/update/$', AdminUpdateProfileView.as_view(),name='admin-cognito-update-user')
)