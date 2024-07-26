from django.urls import path
from chat.consumers import MychatApp,NotificationConsumer

websocket_urlpatterns =[
    path('ws/wsc/',MychatApp.as_asgi()),
    path('ws/notify/',NotificationConsumer.as_asgi())
]