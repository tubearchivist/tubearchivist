"""custom admin classes"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django_celery_beat import models as BeatModels

from .models import Account


class HomeAdmin(BaseUserAdmin):
    """register in admin page"""

    list_display = ("name", "is_staff", "is_superuser")
    list_filter = ("is_superuser",)

    fieldsets = (
        (None, {"fields": ("is_staff", "is_superuser", "password")}),
        ("Personal info", {"fields": ("name",)}),
        ("Groups", {"fields": ("groups",)}),
        ("Permissions", {"fields": ("user_permissions",)}),
    )
    add_fieldsets = (
        (
            None,
            {"fields": ("is_staff", "is_superuser", "password1", "password2")},
        ),
        ("Personal info", {"fields": ("name",)}),
        ("Groups", {"fields": ("groups",)}),
        ("Permissions", {"fields": ("user_permissions",)}),
    )

    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ()


admin.site.register(Account, HomeAdmin)
admin.site.unregister(
    [
        BeatModels.ClockedSchedule,
        BeatModels.CrontabSchedule,
        BeatModels.IntervalSchedule,
        BeatModels.PeriodicTask,
        BeatModels.SolarSchedule,
    ]
)
