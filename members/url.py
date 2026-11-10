from django.urls import path
from .views import register_member, verify_email, login_member, forgot_password, reset_password, membership_plans, my_membership, membership_history

urlpatterns = [
    path('register/', register_member, name='register_member'),
    path('verify-email/', verify_email, name='verify_email'),
    path('login/', login_member, name='login_member'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/', reset_password, name='reset_password'),
    path('membership-plans/', membership_plans, name='membership_plans'),
    path('my-membership/', my_membership, name='my_membership'),
    path('membership-history/', membership_history, name='membership_history'),
]