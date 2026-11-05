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