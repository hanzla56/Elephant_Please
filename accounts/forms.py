
from django.contrib.auth.forms import UserCreationForm
from .models import MyUser
from allauth.account.forms import SignupForm,LoginForm
from django import forms



class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)

        # Remove username and password2 fields
        self.fields.pop('username')
        self.fields.pop('password2')

        # Change label of email field
        self.fields['email'].label = 'Email'

        # Set field order
        self.fields.keyOrder = [
            'first_name',
            'last_name',
            'email',
            'password1'
        ]

        # Remove placeholder attribute from all fields
        for field_name, field in self.fields.items():
            print('sign up form')
            field.widget.attrs.pop('placeholder', None)
            
        self.fields['password1'].widget.attrs.update({'placeholder': 'Should be 8 characters must use special character','class':'placeholder'})

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.username = self.cleaned_data['first_name']
        print(user.username)
        user.last_name = self.cleaned_data['last_name']
        user.save()
        print(user)
        return user
    
    
# class CustomSignupForm(SignupForm):
#     def __init__(self, *args, **kwargs):
#         super(CustomSignupForm, self).__init__(*args, **kwargs)
#         for field_name, field in self.fields.items():
#             field.widget.attrs.pop('placeholder', None)
            

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the 'username' field
        # self.fields.pop('login')
        # self.fields.pop('remember')
        
        # Change label of 'email' field
        self.fields['login'].label = 'Email'
        

        # Remove placeholder attribute from all fields
        for field_name, field in self.fields.items():
            print(field)
            field.widget.attrs.pop('placeholder', None)
            
            
        # self.fields['login'].widget.attrs.update({'placeholder': 'Enter your email'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Should be 8 characters must use special character','class':'placeholder'})