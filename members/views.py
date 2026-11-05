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
from .models import Member, EmailOTP
from .serializers import (
    MemberRegistrationSerializer,
    MemberLoginSerializer
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