from django.urls import path
from .views import register_member, verify_email, login_member

urlpatterns = [
    path('register/', register_member, name='register_member'),
    path('verify-email/', verify_email, name='verify_email'),
    path('login/', login_member, name='login_member'),
]