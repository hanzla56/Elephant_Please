from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserProfileManager(BaseUserManager):
    def create_user(self, email, mobile_number, agree, name, password=None):
        """ Create a new user profile """
        if not email:
            raise ValueError('User must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, name=name,
                          mobile_number=mobile_number, agree=agree)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        """ Create a new superuser profile """
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")
        if not name:
            raise ValueError("User must have a name")
        user = self.model(
            email=self.normalize_email(email)
        )
        # user = self.create_user(email,name,password)
        user.name = name
        user.set_password(password)
        user.email = email
        user.is_superuser = True
        user.is_staff = True
        user.admin = True

        user.save(using=self._db)

        return user