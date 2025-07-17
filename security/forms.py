# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import MyUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = MyUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if MyUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
