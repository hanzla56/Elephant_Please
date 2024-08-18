from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager



class UserProfileManager(BaseUserManager):
    def create_user(self, name, email=None, mobile_number=None, agree=False, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(
            username=name,
            email=email,
            mobile_number=mobile_number,
            agree=agree,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, email, password):
        user = self.create_user(
            name=name,
            email=email,
            password=password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user





# class UserProfileManager(BaseUserManager):
#     def create_user(self, username, email, mobile_number=None, agree=False, name=None, password=None):
#         """Create and return a regular user with an email and username."""
#         if not email:
#             raise ValueError('User must have an email address')
#         if not username:
#             raise ValueError('User must have a username')

#         email = self.normalize_email(email)
#         user = self.model(
#             username=username,
#             email=email,
#             name=name,
#             mobile_number=mobile_number,
#             agree=agree,
#         )

#         user.set_password(password)
#         user.save(using=self._db)

#         return user

#     def create_superuser(self, username, email, password, name=None):
#         """Create and return a superuser with an email and username."""
#         if not email:
#             raise ValueError("Superuser must have an email address")
#         if not username:
#             raise ValueError("Superuser must have a username")
#         if not password:
#             raise ValueError("Superuser must have a password")

#         email = self.normalize_email(email)
#         user = self.model(
#             username=username,
#             email=email,
#             name=name,
#         )
#         user.set_password(password)
#         user.is_superuser = True
#         user.is_staff = True

#         user.save(using=self._db)

#         return user
