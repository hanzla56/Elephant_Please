from django.urls import path
from .views import index,fetch_notifications,mark_as_read

app_name = 'chat'


urlpatterns = [
    path('',index,name='index'),
    path('api/notifications/', fetch_notifications, name='fetch_notifications'),
    path('api/notifications/<int:notification_id>/read/', mark_as_read, name='mark_as_read'),
]
