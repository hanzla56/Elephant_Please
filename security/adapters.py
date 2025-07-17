# In adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        # Call the parent method to save the user
        user = super().save_user(request, sociallogin, form)
        # Set is_active to True for third-party signups
        user.is_active = True
        user.save()
        return user
