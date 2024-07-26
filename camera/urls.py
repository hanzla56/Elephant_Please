from django.contrib import admin
from django.urls import path,include
from camera import views
from camera.views import CreateCheckoutSessionView,stripe_webhook

app_name = 'camera'

urlpatterns = [
    path('',views.Home,name='home_page'),
    path('category/',views.category_page,name='category'),
    path('search-items/', views.search_items, name='search-items'),
    path('detail/<int:p_id>',views.detail,name='detail'),
    path('product/<int:product_id>/add_review/', views.add_review, name='add_review'),
    path('add_item/',views.add_item,name='create'),
    path('edit_item/<int:product_id>/',views.edit_item,name='edit'),
    path('form_submit',views.submission,name='submit'),
    path('profile/',views.profile,name='profile'),
    path('edit_profile/',views.edit_profile,name='edit_profile'),
    path('checkout/',views.checkout,name='checkout'),
    
      
    path('create-checkout-session/<int:id>/',CreateCheckoutSessionView.as_view(),name="create-checkout-session"),
    path('success/<int:p_id>/',views.success_view,name='success'),
    path("stripe_webhooks/",stripe_webhook,name='stripe-webhook'),
]