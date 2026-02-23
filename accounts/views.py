from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .forms import RegisterForm, LoginForm
from .models import AppUser
from accounts.utils import get_post_login_redirect

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'

    def form_valid(self, form):
        user = form.save()

        authenticated_user = authenticate(
            self.request,
            username=user.username,
            password=form.cleaned_data["password1"]
        )

        login(self.request, authenticated_user)

        return redirect(get_post_login_redirect(user))

class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        return get_post_login_redirect(self.request.user)

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('landing-page')