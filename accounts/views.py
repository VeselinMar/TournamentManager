from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.shortcuts import redirect
from .forms import RegisterForm, LoginForm
from .models import AppUser
from accounts.utils import get_post_login_redirect

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(get_post_login_redirect(user))

class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        return get_post_login_redirect(self.request.user)

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')