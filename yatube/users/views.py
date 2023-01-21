from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    # После успешной регистрации перенаправляем пользователя на главную.
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class LogoutView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/logout.html'


class LoginView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/login.html'
