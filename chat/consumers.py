import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer 
from asgiref.sync import async_to_sync
from chat.models import Mychats, Notification
from time import sleep
import datetime
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from channels.layers import get_channel_layer
from camera.views import payment_successful_signal 


User = get_user_model()

def sanitize_group_name(name):
    """
    Sanitize group name to contain only ASCII alphanumerics, hyphens, and periods.
    """
    # Convert to string and replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9\-\.]', '_', str(name))
    return sanitized

class MychatApp(AsyncWebsocketConsumer):
    
    async def connect(self):
        print(f"================== {self.scope['user']}")
        
        # Check if user is authenticated
        if self.scope['user'].is_anonymous:
            await self.close()
            return
            
        await self.accept()
        
        # Sanitize the group name to ensure it only contains valid characters
        user_identifier = sanitize_group_name(self.scope['user'].username or self.scope['user'].id)
        self.group_name = f"mychat_app_{user_identifier}"
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"User {self.scope['user']} joined group: {self.group_name}")
         
         
    async def disconnect(self, close_code):
        # Leave the group when disconnecting
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"User {self.scope['user']} left group: {self.group_name}")
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data = json.loads(text_data)
            
            # Validate required fields
            if 'user' not in text_data or 'msg' not in text_data:
                await self.send(text_data=json.dumps({
                    'error': 'Missing required fields: user and msg'
                }))
                return
            
            # Sanitize the target user group name
            target_user_identifier = sanitize_group_name(text_data['user'])
            target_group = f"mychat_app_{target_user_identifier}"
            
            await self.channel_layer.group_send(
                target_group,
                {
                    'type': 'send_msg',
                    'msg': json.dumps({
                        'user': self.scope['user'].username,
                        'msg': text_data['msg'],
                        'timestamp': str(datetime.datetime.now())
                    })
                }
            )
            
            # Save the chat message
            await self.save_chat(text_data)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            print(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'error': 'An error occurred while processing your message'
            }))

    @database_sync_to_async   
    def save_chat(self, text_data):
        try:
            print('Entering save_chat function')
            print(f'Text data: {text_data}')
            
            # Get the friend user
            try:
                frnd = User.objects.get(username=text_data['user'])
            except User.DoesNotExist:
                print(f"User {text_data['user']} does not exist")
                return
            
            current_time = str(datetime.datetime.now())
            
            # Save chat for the sender (me)
            mychats, created = Mychats.objects.get_or_create(
                me=self.scope['user'], 
                frnd=frnd
            )
            if created or not mychats.chats:
                mychats.chats = {}
            
            mychats.chats[current_time + "_1"] = {
                'user': 'me', 
                'msg': text_data['msg'],
                'timestamp': current_time
            }
            mychats.save()
            
            # Save chat for the receiver (friend)
            mychats_frnd, created = Mychats.objects.get_or_create(
                me=frnd, 
                frnd=self.scope['user']
            )
            if created or not mychats_frnd.chats:
                mychats_frnd.chats = {}
                
            mychats_frnd.chats[current_time + "_2"] = {
                'user': frnd.username, 
                'msg': text_data['msg'],
                'timestamp': current_time
            }
            mychats_frnd.save()
            
            print('Chat data has been saved successfully')
            
        except Exception as e:
            print(f"Error saving chat: {e}")
        
    async def send_videonofication(self, event):
        await self.send(text_data=event['msg'])

    async def send_msg(self, event):
        print(f"Sending message: {event['msg']}")
        await self.send(text_data=event['msg'])
        
    async def chat_message(self, event):
        print(f"Chat message: {event['message']}")
        await self.send(text_data=json.dumps({
            "message": "Total Online: " + str(event['message'])
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated
        if self.scope['user'].is_anonymous:
            await self.close()
            return
            
        self.user = self.scope['user']
        # Use user ID instead of email for group name to avoid special characters
        self.group_name = f"user_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connection established for user: {self.user.id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            print(f"WebSocket connection closed for user: {self.user.id}")

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'timestamp': str(datetime.datetime.now())
        }))


def send_payment_notification(sender, user_id, product, **kwargs):
    """
    Send payment notifications to both buyer and seller
    """
    try:
        product_name = product.title
        owner_id = product.owner.id
        print(f'Product owner ID: {owner_id}')
        print(f'Notification for product: {product_name}')
        
        owner_message = f"Congrats! You received a new order for {product_name}"
        user_message = f"Payment successful for {product_name}"
        
        # Save notifications to database
        Notification.objects.create(user_id=owner_id, message=owner_message)
        Notification.objects.create(user_id=user_id, message=user_message)

        async def send_notification_to_users():
            channel_layer = get_channel_layer()
            print('Channel layer initialized')
            
            # Send notification to product owner
            await channel_layer.group_send(
                f"user_{owner_id}",
                {
                    'type': 'send_notification',
                    'message': owner_message
                }
            )
            print('Message sent to owner group')
            
            # Send notification to buyer
            await channel_layer.group_send(
                f"user_{user_id}",
                {
                    'type': 'send_notification',
                    'message': user_message
                }
            )
            print('Message sent to buyer group')

        # Execute the async function in sync context
        async_to_sync(send_notification_to_users)()
        print('Notifications sent successfully')
        
    except Exception as e:
        print(f"Error sending payment notification: {e}")


# Connect the signal
@receiver(payment_successful_signal)
def connect_payment_signal(sender, **kwargs):
    print(f"Signal received for user: {kwargs.get('user_id')} and product: {kwargs.get('product').title}")
    send_payment_notification(sender, **kwargs)