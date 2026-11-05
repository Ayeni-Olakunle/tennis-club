from rest_framework import serializers
from .models import Member

class MemberRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )
    class Meta:
        model = Member
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'date_of_birth',
            'membership_start_date',
            'membership_end_date',
            'password',
            'created_at',
            'updated_at'
        ]

        read_only_fields = ['id']

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password

        validated_data['password'] = make_password(
            validated_data['password']
        )

        validated_data['is_active'] = False

        return Member.objects.create(**validated_data)


class MemberLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.strip().lower()