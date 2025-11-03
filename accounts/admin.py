from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "DDPS Access",
            {
                "fields": (
                    "role",
                    "can_view_finance",
                    "can_view_programme",
                    "can_view_technical",
                    "can_view_client_details",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "role",
        "can_view_finance",
        "can_view_programme",
    )
    list_filter = ("role", "can_view_finance", "can_view_programme")
