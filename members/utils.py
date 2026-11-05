import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import (
    make_password,
    check_password
)
from django.utils import timezone

from .models import EmailOTP


def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def send_member_otp(member, purpose):

    # Invalidate previous unused OTPs for this purpose
    EmailOTP.objects.filter(
        member=member,
        purpose=purpose,
        is_used=False
    ).update(is_used=True)

    otp = generate_otp()

    EmailOTP.objects.create(
        member=member,
        otp_hash=make_password(otp),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    if purpose == EmailOTP.REGISTRATION:
        subject = 'Verify Your Email Address'
        message = (
            f'Hello {member.first_name},\n\n'
            f'Your email verification OTP is: {otp}\n\n'
            'This code expires in 5 minutes.\n'
            'Do not share this code with anyone.'
        )

    else:
        subject = 'Password Reset OTP'
        message = (
            f'Hello {member.first_name},\n\n'
            f'Your password reset OTP is: {otp}\n\n'
            'This code expires in 5 minutes.\n'
            'Do not share this code with anyone.'
        )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [member.email],
        fail_silently=False
    )


def verify_member_otp(member, otp, purpose):

    otp_record = EmailOTP.objects.filter(
        member=member,
        purpose=purpose,
        is_used=False
    ).order_by('-created_at').first()

    if not otp_record:
        return False, 'No valid OTP found. Request a new OTP.'

    if otp_record.expires_at <= timezone.now():
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])

        return False, 'OTP has expired. Request a new OTP.'

    if otp_record.attempts >= 5:
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])

        return False, 'Too many attempts. Request a new OTP.'

    if not check_password(otp, otp_record.otp_hash):

        otp_record.attempts += 1
        otp_record.save(update_fields=['attempts'])

        return False, 'Incorrect OTP.'

    otp_record.is_used = True
    otp_record.save(update_fields=['is_used'])

    return True, 'OTP verified successfully.'