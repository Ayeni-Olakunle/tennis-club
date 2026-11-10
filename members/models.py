from django.db import models
from django.utils import timezone

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

    @property
    def is_authenticated(self):
        return True

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



class MembershipPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    member = models.ForeignKey(
        'Member',
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name='memberships'
    )

    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member} - {self.plan.name}"
