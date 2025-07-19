from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.conf import settings

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from django.contrib.auth.tokens import default_token_generator
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .utils import clean_spaces,validate_and_clean_spaces

import random
import string
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta

from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm


User = get_user_model()

def send_otp(request):
    print('otp topt p')
    if request.method == "POST":
        email = request.POST.get('email')
        print(email)
        print('otp function runs')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "This email does not exist.")
            return render(request, 'security/forgetPassword.html')


        if email:
            # Generate a random 4-digit OTP
            print('dfdffdfdfff')
            otp = ''.join(random.choices(string.digits, k=6))
            otp_expiry = timezone.now() + timedelta(minutes=2)  # OTP is valid for 2 minutes

            # Save OTP and expiry in session (or save in the database for more robust handling)
            request.session['otp'] = otp
            request.session['otp_expiry'] = otp_expiry.strftime("%Y-%m-%d %H:%M:%S")
            request.session['email'] = email

            # Send OTP via email
            try:
                send_mail(
                subject='Your OTP for Password Reset',
                message=f'Your OTP for password reset is {otp}. It is valid for 2 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
                messages.success(request, "OTP has been sent to your email. It is valid for 2 minutes.")
                return redirect('security:verify-otp')  # Replace with your OTP verification view
            
            except:
                print("Email sending failed:", e)
                messages.error(request, "Failed to send OTP email. Please try again later.")
                return redirect('security:forgot-password')
                
    
            return render(request, 'security/otp.html')

    return render(request, 'otp.html')

def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        print(f'this is enter otp {entered_otp}')


        # Retrieve the saved OTP and expiry time from the session
        session_otp = request.session.get('otp')
        print(f'this is session otp {session_otp}')
       
        otp_expiry_str = request.session.get('otp_expiry')

        # Convert the expiry time string back to a datetime object
        otp_expiry = datetime.strptime(otp_expiry_str, "%Y-%m-%d %H:%M:%S")

        # Make the otp_expiry timezone-aware by adding the correct timezone
        otp_expiry = timezone.make_aware(otp_expiry, timezone.get_current_timezone())

        # Check if the OTP has expired
        if timezone.now() > otp_expiry:
            messages.error(request, "The otp has expired.")
            return render(request, 'security/otp.html')

        # Verify if the entered OTP matches the one in session
        if entered_otp == session_otp:
            messages.success(request, "Congrats your otp has been matched.")
            return render(request, 'security/resetPassword.html')
        else:
            messages.error(request, "invalid otp.")
            return render(request, 'security/otp.html')

    return render(request, 'security/otp.html')
    
    
def reset_password(request):
    print('reset passowrd')
    if request.method == "POST":
        print('reset')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        print(f'the new password {new_password} and the confirm password is {confirm_password}')

        # Check if passwords match
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'security/resetPassword.html')
        
        print('reset passowrd')

        # Retrieve email from session
        email = request.session.get('email')

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            messages.error(request, "User does not exist.")
            return render(request, 'security/resetPassword.html')

        # Update the user's password
        print(f"Before set_password: {user.password}")
        user.set_password(new_password)
        print(f"After set_password: {user.password}")

        user.save()
        
        print(f'the usre is this after password change {user}')

        # Clear session data
        request.session.pop('otp', None)
        request.session.pop('otp_expiry', None)
        request.session.pop('email', None)

        messages.success(request, "Your password has been reset successfully.")
        return redirect('security:login')

    return render(request, 'security/resetPassword.html')     


def send_verification_email(request, user):
    """
    Sends an account verification email to the user with a tokenized link.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = request.get_host()
    
    link = f"http://{domain}/account/verify/{uid}/{token}/"

    subject = "Activate Your Account"
    message = f"""
        Hi {user.username},

        Thank you for registering. Please click the link below to confirm your email address:

        {link}

        Thank you!
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
             

def register_view(request):
    if request.method == 'POST':
        print('inside view')
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    send_verification_email(request, user)

                    messages.success(
                        request,
                        "Registration successful! Please check your email to activate your account."
                    )
                    return redirect('security:login')
            except Exception as e:
                print(e)
                messages.error(request, f"Unexpected error: {e}")
                return redirect('security:signup')
        else:
            print('in else view')
            print(form.errors.as_json())

            # Collect and display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return redirect('security:signup')

    else:
        return render(request, 'security/signup.html')


# @csrf_exempt
# def register_view(request):  
#     if request.method == 'POST':
#         try:
#             with transaction.atomic():        
#                 print(request.POST) 
#                 print('in the view')
#                 data = request.POST   #Assign data into data variable
                
#                 email = validate_and_clean_spaces(data['email'],'Email')
#                 first_name = validate_and_clean_spaces(data['first_name'],'First Name')
#                 last_name = validate_and_clean_spaces(data['last_name'],'Last Name')
#                 password = data['password'].strip()  # keep .strip() fordata
                
#                 if first_name == last_name:
#                     messages.error(request, "first_name and last_name should not match.")
#                     return redirect('security:signup')

#                 if User.objects.filter(email__iexact=email).exists():
#                     messages.error(request, "Email is already taken.")
#                     return redirect('security:signup')
                
#                 # Password strength validation
#                 validate_password(password)

#                 user = User(email=email, last_name=last_name, first_name=first_name, password=password,is_active=False)
#                 user.full_clean()  # ✅ Run all model field and clean() validation
#                 user.save()
                
#                 token = default_token_generator.make_token(user)
#                 uid = urlsafe_base64_encode(force_bytes(user.pk))
#                 domain = request.get_host()
#                 link = f"http://{domain}/security/verify/{uid}/{token}/"

#                 subject = "Activate Your Account"
#                 message = f"""
#                 Hi {user.first_name},

#                 Thank you for registering. Please click the link below to confirm your email address:

#                 {link}

#                 Thank you!
#                 """

#                 # Send email
#                 send_mail(
#                     subject,
#                     message,
#                     settings.DEFAULT_FROM_EMAIL,
#                     [email],
#                     fail_silently=False,
#                 )

#                 messages.success(request, "Registration successful. You can log in after clicking the given link we have sent to your email.")
#                 return redirect('security:login') 
            
#         except ValidationError as e:
#             if hasattr(e, 'message_dict'):
#                 for field, error_list in e.message_dict.items():
#                     for error in error_list:
#                         messages.error(request, f"{field.capitalize()}: {error}")
#             else:
#                 # fallback for non-field errors
#                 for error in e.messages:
#                     messages.error(request, error)
#             return redirect('security:signup')
        
#         except Exception as e:
#             #    messages.error(request, "Something went wrong. Please try again.")
#                messages.error(request,e)
#                return redirect('security:signup')    
#     else:
#         return render(request, 'security/signup.html')
    
    

def activate_account(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(f'the user is {user}')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save()
        # User.objects.filter(pk=user.pk).update(is_active=True)
        print('update')
        print(f'the email link verififd {user.email_verified}')
        messages.success(request, "Your account has been activated. You can now log in.")
        return redirect('security:login')
    else:
        messages.error(request, "The activation link is invalid.")
        return redirect('security:register')

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('email')
        password = request.POST['password']
        print(username_or_email)
        print(password)
        
        User = get_user_model()

        try:
            user = User.objects.get(email=username_or_email)
            print(f'the use is : {user}')
        except User.DoesNotExist:
            user = None

        if user is not None:
            if not user.email_verified:
                messages.error(request, "Please verify your email before logging in.")
                return redirect('security:login')
        
        user = authenticate(request, username=username_or_email, password=password)
        print(f'the user is {user}')
        
        if user is not None:
            if user.email_verified:  
                auth_login(request, user)
                messages.success(request, "Login successful.")
                print("Logged in successfully")
                # Fetch the user's plan
                # try:
                #     user_plan = UserPlan.objects.get(user=user)
                #     print(user_plan.user)
                #     print(f"User plan: {user_plan.package.name}")
                #     # You can also store it in session if you want to use it later
                #     request.session['user_plan'] = user_plan.package.name
                #     return redirect('dashboard:events')
                # except UserPlan.DoesNotExist:
                #     print("No plan found for this user.")
                #     messages.warning(request, "No active plan found.")
                #     return redirect('websiteDesign:pricing')
                return redirect('Quote:home')
                
            else:
                messages.error(request, "Please verify your email before logging in.")
                return redirect('security:login')
        else:
            messages.error(request, "Invalid email or password.")
            print("Login failed")
            return redirect('security:login')
    
    return render(request, 'security/login.html')



def signup_view(request):
    return render(request, 'security/signup.html')


def login(request):
      return render(request,"security/login.html")


def signup(request):
      return render(request,"security/signup.html")


def logout_view(request):
    logout(request)
    return redirect('security:login')


def forgot_view(request):
    return render(request, 'security/forgetPassword.html')

def otp_view(request):
    return render(request, 'security/otp.html')