from django.urls import path
from .views import register_member, verify_email, login_member, forgot_password

urlpatterns = [
    path('register/', register_member, name='register_member'),
    path('verify-email/', verify_email, name='verify_email'),
    path('login/', login_member, name='login_member'),
    path('forgot-password/', forgot_password, name='forgot_password'),
]