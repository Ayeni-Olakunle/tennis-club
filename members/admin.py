
from django.contrib import admin
from .models import Member, MembershipPlan, Membership


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'is_active',
    )
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'duration_days',
        'price',
        'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'plan',
        'start_date',
        'end_date',
        'status',
    )
    list_filter = ('status', 'plan')
    search_fields = ('member__email',)
