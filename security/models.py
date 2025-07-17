from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from .utils import clean_spaces

# Create your models here.
class MyUserManager(BaseUserManager):
    def create_user(self,username, email, password=None, **extra_fields):
        print('running create user function')
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email).lower()
        user = self.model(username=username ,email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,username, email, password=None, **extra_fields):
        print('running superuser function')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)
  
  
class MyUser(AbstractUser):
    first_name = None  # Remove the username field
    last_name = None
    email = models.EmailField(unique=True)  # Ensure email is unique
    username = models.CharField(max_length=50)
    email_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    

    USERNAME_FIELD = 'email'  # Use email to log in
    REQUIRED_FIELDS = ['username']  # Fields required when creating a superuser
    
    objects = MyUserManager()  # Use your custom manager


    def __str__(self):
        return self.email
    
    # def clean(self):
    #     super().clean()
    #     self.first_name = clean_spaces(self.first_name)
    #     self.last_name = clean_spaces(self.last_name)
        

        # if not self.first_name:
        #     raise ValidationError({'first_name': 'First name cannot be empty or only spaces.'})
        # if not self.last_name:
        #     raise ValidationError({'last_name': 'Last name cannot be empty or only spaces.'})
  
  
  

