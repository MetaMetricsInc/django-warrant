from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from django_warrant.views.mixins import GetUserMixin, TokenMixin

try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.contrib.auth.views import LogoutView as DJLogoutView


from django_warrant.forms import ProfileForm


class ProfileView(LoginRequiredMixin,TokenMixin,GetUserMixin,TemplateView):
    template_name = 'warrant/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['user'] = self.get_user()
        return context


class UpdateProfileView(LoginRequiredMixin,TokenMixin,GetUserMixin,FormView):
    template_name = 'warrant/update-profile.html'
    form_class = ProfileForm

    def get_success_url(self):
        return reverse_lazy('dw:profile')

    def get_initial(self):
        self.user = self.get_user()
        return self.user._data
    
    def form_valid(self, form):
        if not self.user:
            self.user = self.get_user()
        self.user._data = form.cleaned_data
        self.user.save()
        messages.success(self.request,'You have successfully updated your profile.')
        return super(UpdateProfileView, self).form_valid(form)


class LogoutView(DJLogoutView):

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        request.session.delete()
        return super(LogoutView, self).dispatch(request, *args, **kwargs)