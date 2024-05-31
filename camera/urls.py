from django.contrib import admin
from django.urls import path,include
from camera import views

app_name = 'camera'

urlpatterns = [
    path('',views.category_page,name='category'),
    path('detail/',views.detail,name='detail'),
    path('add_item/',views.add_item,name='create'),
    path('edit_item/<int:product_id>/',views.edit_item,name='edit'),
    path('form_submit',views.submission,name='submit')
]