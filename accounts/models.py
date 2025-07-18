from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class AppUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    

class AppUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        unique=True,
    )
    date_joined = models.DateTimeField(
        default=timezone.now
    )
    is_active = models.BooleanField(
        default=True
    )
    is_staff = models.BooleanField(
        default=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = AppUserManager()

    def __str__(self):
        return self.email