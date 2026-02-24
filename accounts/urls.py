from django.urls import path
from .views import RegisterView, UserLoginView, UserLogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('custom-login/', UserLoginView.as_view(), name='custom-login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
