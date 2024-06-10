from django.db import models

# Create your models here.


from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings
from django.db import models
from django.db.models import SET

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

User = get_user_model()

class Message(models.Model):
    sender_user = models.ForeignKey(User, related_name='sender', on_delete=models.SET(settings.ANONYMOUS_USER_ID),default="")
    receiver_user = models.ForeignKey(User, related_name='receiver', on_delete=models.SET(settings.ANONYMOUS_USER_ID), default="")
    message = models.TextField(default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender_user} to {self.receiver_user}'

class Room(models.Model):
    sender_user = models.ForeignKey(User, related_name='room_sender', on_delete=models.SET(settings.ANONYMOUS_USER_ID), default="")
    receiver_user = models.ForeignKey(User, related_name='room_receiver', on_delete=models.SET(settings.ANONYMOUS_USER_ID), default="")
    room_name = models.CharField(max_length=200, unique=True,default="")

    def __str__(self):
        return self.room_name
