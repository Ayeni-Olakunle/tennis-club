from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Member


class MemberJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):

        member_id = validated_token.get('member_id')

        if not member_id:
            raise AuthenticationFailed(
                'Token does not contain member ID.'
            )

        try:
            member = Member.objects.get(
                id=member_id,
                is_active=True
            )

        except Member.DoesNotExist:
            raise AuthenticationFailed(
                'Member not found or account is inactive.'
            )

        return member