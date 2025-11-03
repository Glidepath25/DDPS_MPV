from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user that supports role-based views of project information.
    """

    class Role(models.TextChoices):
        INTERNAL = "internal", "Internal"
        SIKLA = "sikla", "Sikla"
        CLIENT = "client", "Client"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.INTERNAL,
        help_text="Determines the default scope of accessible projects.",
    )
    can_view_finance = models.BooleanField(default=False)
    can_view_programme = models.BooleanField(default=True)
    can_view_technical = models.BooleanField(default=True)
    can_view_client_details = models.BooleanField(default=True)

    @property
    def is_client_user(self) -> bool:
        return self.role == self.Role.CLIENT
