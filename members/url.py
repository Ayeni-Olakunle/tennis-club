from django.urls import path
from .views import register_member

urlpatterns = [
    path('register/', register_member, name='register_member'),
]