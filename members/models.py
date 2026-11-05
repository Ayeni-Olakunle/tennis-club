from django.db import models

# Create your models here.
class Member(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    membership_start_date = models.DateField(blank=True, null=True)
    membership_end_date = models.DateField(blank=True, null=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class EmailOTP(models.Model):

    REGISTRATION = 'registration'
    PASSWORD_RESET = 'password_reset'

    PURPOSE_CHOICES = [
        (REGISTRATION, 'Registration'),
        (PASSWORD_RESET, 'Password Reset'),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='email_otps'
    )

    otp_hash = models.CharField(max_length=128)

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(default=0)

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.email} - {self.purpose}"