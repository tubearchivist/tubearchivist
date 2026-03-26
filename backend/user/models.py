"""custom models"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class AccountManager(BaseUserManager):
    """manage user creation methods"""

    use_in_migrations = True

    def _create_user(self, name, password, **extra_fields):
        """create regular user private"""
        if not name:
            raise ValueError("The name value must be set")
        if not password:
            raise ValueError("The password value must be set")

        user = self.model(name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, name, password):
        """create regular user public"""
        return self._create_user(name, password)

    def create_superuser(self, name, password, **extra_fields):
        """create super user"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(name, password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin):
    """handle account creation"""

    name = models.CharField(max_length=150, unique=True)
    is_staff = models.BooleanField(default=False)
    objects = AccountManager()

    USERNAME_FIELD = "name"
    REQUIRED_FIELDS = []
