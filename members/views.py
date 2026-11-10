from django.contrib.auth.hashers import (
    check_password,
    make_password
)
from django.utils import timezone
from rest_framework.decorators import (
    api_view,
    permission_classes
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db import transaction
from datetime import timedelta
from .models import Member, EmailOTP, MembershipPlan, Membership
from .serializers import (
    MemberRegistrationSerializer,
    MemberLoginSerializer,
    MembershipPlanSerializer,
    MembershipSerializer,
    RenewMembershipSerializer
)
from .utils import (
    send_member_otp,
    verify_member_otp
)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_member(request):

    serializer = MemberRegistrationSerializer(
        data=request.data
    )

    if serializer.is_valid():

        email = serializer.validated_data['email']

        if Member.objects.filter(email__iexact=email).exists():
            return Response({
                'message': 'Email already registered.'
            }, status=status.HTTP_400_BAD_REQUEST)

        member = serializer.save()

        try:
            send_member_otp(
                member,
                EmailOTP.REGISTRATION
            )

        except Exception:
            member.delete()

            return Response({
                'message': 'Unable to send verification email. Please try again.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            'message': 'Registration successful. Check your email for the OTP.',
            'email': member.email
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):

    email = request.data.get('email', '').strip().lower()

    otp = request.data.get('otp', '')

    if not email or not otp:
        return Response({
            'message': 'Email and OTP are required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not otp.isdigit() or len(otp) != 6:
        return Response({
            'message': 'OTP must contain exactly 6 digits.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        member = Member.objects.get(email__iexact=email)

    except Member.DoesNotExist:
        return Response({
            'message': 'Invalid verification request.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if member.is_active:
        return Response({
            'message': 'Email already verified.'
        }, status=status.HTTP_400_BAD_REQUEST)

    success, message = verify_member_otp(
        member,
        otp,
        EmailOTP.REGISTRATION
    )

    if not success:
        return Response({
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)

    member.is_active = True

    member.save(update_fields=['is_active'])

    return Response({
        'message': 'Email verified successfully. You can now log in.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_member(request):

    serializer = MemberLoginSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data['email']

    password = serializer.validated_data['password']

    try:
        member = Member.objects.get(
            email__iexact=email
        )

    except Member.DoesNotExist:
        return Response({
            'message': 'Invalid email or password.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    if not check_password(password, member.password):
        return Response({
            'message': 'Invalid email or password.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    if not member.is_active:
        return Response({
            'message': 'Please verify your email before logging in.'
        }, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken()

    refresh['member_id'] = member.id

    refresh['email'] = member.email

    return Response({
        'message': 'Login successful',

        'member': {
            'id': member.id,
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'phone_number': member.phone_number
        },

        'refresh': str(refresh),

        'access': str(refresh.access_token)

    }, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):

    email = request.data.get('email', '').strip().lower()

    if not email:
        return Response({
            'message': 'Email is required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        member = Member.objects.get(
            email__iexact=email,
            is_active=True
        )

    except Member.DoesNotExist:
        # Same response prevents revealing whether an account exists.
        return Response({
            'message': 'If the account exists, a password reset OTP will be sent.'
        }, status=status.HTTP_200_OK)

    try:
        send_member_otp(
            member,
            EmailOTP.PASSWORD_RESET
        )

    except Exception:
        return Response({
            'message': 'Unable to send OTP. Please try again.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'message': 'If the account exists, a password reset OTP will be sent.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):

    if not isinstance(request.data, dict):
        return Response(
            {'error': 'Request body must be a JSON object.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = request.data.get('email', '').strip().lower()
    otp = request.data.get('otp', '').strip()
    new_password = request.data.get('new_password', '')

    if not email or not otp or not new_password:
        return Response(
            {'error': 'Email, OTP and new password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        member = Member.objects.get(email=email, is_active=True)
    except Member.DoesNotExist:
        return Response(
            {'error': 'Invalid email or OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {'error': 'Password must contain at least 8 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not verify_member_otp(member, otp, 'password_reset'):
        return Response(
            {'error': 'Invalid or expired OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    member.password = make_password(new_password)
    member.save(update_fields=['password'])

    return Response(
        {'message': 'Password reset successfully.'},
        status=status.HTTP_200_OK
    )




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def membership_plans(request):

    plans = MembershipPlan.objects.filter(
        is_active=True
    ).order_by('price')

    serializer = MembershipPlanSerializer(
        plans,
        many=True
    )

    return Response({
        'message': 'Available membership plans.',
        'plans': serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_membership(request):

    today = timezone.localdate()

    # Automatically mark expired memberships.
    Membership.objects.filter(
        member=request.user,
        status='active',
        end_date__lt=today
    ).update(status='expired')

    membership = Membership.objects.filter(
        member=request.user,
        status='active',
        end_date__gte=today
    ).select_related('plan').order_by('-end_date').first()

    if not membership:
        return Response({
            'message': 'You do not have an active membership.',
            'membership': None
        }, status=status.HTTP_200_OK)

    serializer = MembershipSerializer(membership)

    return Response({
        'message': 'Your current membership.',
        'membership': serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def membership_history(request):

    today = timezone.localdate()

    Membership.objects.filter(
        member=request.user,
        status='active',
        end_date__lt=today
    ).update(status='expired')

    memberships = Membership.objects.filter(
        member=request.user
    ).select_related('plan').order_by('-created_at')

    serializer = MembershipSerializer(
        memberships,
        many=True
    )

    return Response({
        'message': 'Your membership history.',
        'total_memberships': memberships.count(),
        'history': serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renew_membership(request):

    serializer = RenewMembershipSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    plan_id = serializer.validated_data['plan_id']

    try:
        plan = MembershipPlan.objects.get(
            id=plan_id,
            is_active=True
        )
    except MembershipPlan.DoesNotExist:
        return Response(
            {'error': 'Selected membership plan is unavailable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    today = timezone.localdate()

    with transaction.atomic():

        # Mark previous expired memberships.
        Membership.objects.filter(
            member=request.user,
            status='active',
            end_date__lt=today
        ).update(status='expired')

        # Find the latest membership that has not been cancelled.
        previous_membership = Membership.objects.filter(
            member=request.user
        ).exclude(
            status='cancelled'
        ).order_by('-end_date').first()

        # Continue after the previous expiry date if it is still valid.
        if (
            previous_membership
            and previous_membership.end_date >= today
        ):
            start_date = previous_membership.end_date + timedelta(days=1)
        else:
            start_date = today

        end_date = start_date + timedelta(
            days=plan.duration_days - 1
        )

        new_membership = Membership.objects.create(
            member=request.user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )

    result = MembershipSerializer(new_membership)

    return Response({
        'message': 'Membership successfully purchased or renewed.',
        'membership': result.data
    }, status=status.HTTP_201_CREATED)
