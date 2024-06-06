from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.files import File
from PIL import Image, ImageDraw
from django.contrib.auth.hashers import make_password, check_password
from accounts.manager import UserProfileManager
from django.utils import timezone
from datetime import timedelta

class MyUser(AbstractBaseUser, PermissionsMixin):
    mobile_number = models.CharField(max_length=10, blank=True, null=True)
    agree = models.BooleanField(default=False, blank=True)
    forget_password_token = models.CharField(max_length=300, blank=True)
    profile_img = models.ImageField(
        upload_to='profile_imgs', null=True, blank=True,default="{% static 'image/nav/profile.png' %}")


    title = models.CharField(max_length=100, null=True, blank=True)
    age = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100,  null=True, blank=True)
    location = models.CharField(max_length=100,  null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=30, default=None, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(null=True, default=timezone.now)
    is_staff = True
    objects = UserProfileManager()

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['name']


    def save(self, *args, **kwargs):
            if not self.created_at:
                self.created_at = timezone.now()
            super(MyUser, self).save(*args, **kwargs)

    def _str_(self):
        return self.name


    def days_since_creation(self):
        return (timezone.now() - self.created_at).days



