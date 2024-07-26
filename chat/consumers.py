import json
from channels.generic.websocket import AsyncWebsocketConsumer 
from asgiref.sync import async_to_sync
from chat.models import Mychats
from time import sleep
import datetime
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from channels.layers import get_channel_layer
from camera.views import payment_successful_signal 


User = get_user_model()
class MychatApp(AsyncWebsocketConsumer):
    
    async def connect(self):
        print(f"================== {self.scope['user']}")
        await self.accept() 
        await self.channel_layer.group_add(f"mychat_app_{self.scope['user']}", self.channel_name)
         
         
    async def disconnect(self, close_code): 
        pass
    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data = json.loads(text_data)
        await self.channel_layer.group_send(
            f"mychat_app_{text_data['user']}",
            {
                'type':'send.msg',
                'msg':text_data['msg']
            }
            )
        await self.save_chat(text_data)

    @database_sync_to_async   
    def save_chat(self,text_data):
        print('we enter into the save chat function')
        frnd = User.objects.get(username=text_data['user'])
        mychats, created = Mychats.objects.get_or_create(me=self.scope['user'], frnd=frnd)
        # If the object was just created, initialize the 'chats' field as an empty dictionary
        if created:
            mychats.chats = {}
        mychats.chats[str(datetime.datetime.now())+"1"] = {'user': 'me', 'msg': text_data['msg']}
        mychats.save()
        mychats, created = Mychats.objects.get_or_create(me=frnd, frnd=self.scope['user'])
        # If the object was just created, initialize the 'chats' field as an empty dictionary
        if created:
            mychats.chats = {}
        mychats.chats[str(datetime.datetime.now())+"2"] = {'user': frnd.username, 'msg': text_data['msg']}
        mychats.save()
        print('data has been saved')
        
    async def send_videonofication(self,event):
        await  self.send(event['msg'])

    async def send_msg(self,event):
        print(event['msg'])
        await  self.send(event['msg'])
    async def chat_message(self, event):
        print(event['message'])
        await self.send(json.dumps("Total Online :- "+str(event['message'])))
  
  
# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope['user']  # Assuming user is authenticated
#         channel_name = self.channel_name
#         await self.accept()

#     async def disconnect(self, close_code):
#         pass  # No group management needed in this approach

#     async def send_notification(self, event):
#         await self.send(text_data=json.dumps({ 'message': event['message'] }))
        
  
# def send_payment_notification(sender, user_id, product, **kwargs):
#     product_owner = product.owner
#     group_name = f"product_{product_owner.id}"
#     print(f'product owner is {product_owner}')

#     async def send_notification_to_group():
#         channel_layer = get_channel_layer()
#         # Check if group exists before sending (optional)
#         try:
#             await channel_layer.group_check(group_name)
#         except:
#             # Create the group if it doesn't exist
#             print(f"Group '{group_name}' not found. Creating it.")
#             await channel_layer.group_add(group_name)

#         await channel_layer.group_send(
#             group_name,
#             {
#                 'type': 'send_notification',
#                 'message': f"Payment successful for {product.name}"
#             }
#         )

#     async_to_sync(send_notification_to_group)()
    
# # Connect the signal
# @receiver(payment_successful_signal)
# def connect_payment_signal(sender, **kwargs):
#     print(f"Signal received for user: {kwargs.get('user_id')} and product: {kwargs.get('product').title}")  # Add this line
#     send_payment_notification(sender, **kwargs)
      

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']  # Assuming user is authenticated
        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connection established for user: {self.user.id}")  # Add this line

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket connection closed for user: {self.user.id}")  # Add this line

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({ 'message': event['message'] }))


# This function can potentially be a regular function (not async def)
def send_payment_notification(sender, user_id, product, **kwargs):
    product_name = product.title
    owner_id = product.owner.id
    print(f'this is product owner id {owner_id}')
    print(f'the socket connection receive to consumer {product_name}')

    async def send_notification_to_user():
        channel_layer = get_channel_layer()
        print(channel_layer)
        print('channel layer is executed')
        await channel_layer.group_send(
            f"user_{user_id}",
            {
                'type': 'send_notification',
                'message': f"Payment successful for {product_name}"
            }
        )
        print('message is sent to the group')

    async_to_sync(send_notification_to_user)() 
    print('after the channel layer') # Execute the async function in sync context

# Define your signal (assuming you have one)
 # Replace with your actual import path

# Connect the signal
@receiver(payment_successful_signal)
def connect_payment_signal(sender, **kwargs):
    print(f"Signal received for user: {kwargs.get('user_id')} and product: {kwargs.get('product').title}")  # Add this line
    send_payment_notification(sender, **kwargs)
