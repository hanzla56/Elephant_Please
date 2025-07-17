from django.contrib import admin
from django.urls import path,include
from .views import *

app_name = 'security'

urlpatterns = [
    # path('login/',login,name='login'),
    # path('signup/',signup,name='signup'),
    
    path('', register_view , name='register'),
    path('logout/', logout_view, name='logout'),
    path('sign-up/', register_view , name='signup'),
    path('login/', login_view , name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_view, name='forgot-password'),
    path('otp/', otp_view, name='otp'),
    
    path('send-otp/', send_otp, name='send-otp'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('reset-password/', reset_password, name='reset-password'),
 
    path('verify/<uidb64>/<token>/', activate_account, name='activate'),
]
