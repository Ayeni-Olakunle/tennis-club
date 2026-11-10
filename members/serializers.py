from rest_framework import serializers
from .models import Member, MembershipPlan, Membership

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



class MembershipPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = MembershipPlan
        fields = [
            'id',
            'name',
            'description',
            'duration_days',
            'price',
        ]


class MembershipSerializer(serializers.ModelSerializer):

    plan = MembershipPlanSerializer(read_only=True)
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = [
            'id',
            'member_name',
            'plan',
            'start_date',
            'end_date',
            'status',
            'created_at',
        ]

    def get_member_name(self, obj):
        return f"{obj.member.first_name} {obj.member.last_name}"


class RenewMembershipSerializer(serializers.Serializer):

    plan_id = serializers.IntegerField()

    def validate_plan_id(self, value):
        try:
            plan = MembershipPlan.objects.get(
                id=value,
                is_active=True
            )
        except MembershipPlan.DoesNotExist:
            raise serializers.ValidationError(
                "This membership plan does not exist or is unavailable."
            )

        return value
