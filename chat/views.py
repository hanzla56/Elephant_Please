from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.views import View
from chat.models import Room, Message


User = get_user_model()
print(User)

class GetAllUsers(LoginRequiredMixin, View):
    def get(self, request):
        # To get the list of all users from the database
        print(request.user)
        users = User.objects.all()
        print(users)
        return render(request, 'chat/all_users.html', {'users': users})
    
    def post(self, request):
        # To get the sender and receiver users and connect them with their respective room
        sender = request.user.id
        print(f'this is sender {sender}')
        receiver = request.POST['users']
        print(f'this is receive {receiver}')
        sender_user = User.objects.get(id=sender)
        receiver_user = User.objects.get(id=receiver)
        
        # Setting the receiver as a session variable
        request.session['receiver_user'] = receiver
        
        # Check if the sender and receiver already have a room
        get_room = Room.objects.filter(
            Q(sender_user =sender_user, receiver_user=receiver_user) |
            Q(sender_user= receiver_user, receiver_user=sender_user)
        ).first()
        
        # Fetch the room name if a room already exists
        if get_room:
            room_name = get_room.room_name
        else:
            # Create a new room if a room doesn't exist
            new_room = get_random_string(18)
            while True:
                room_exists = Room.objects.filter(room_name=new_room).exists()
                if room_exists:
                    new_room = get_random_string(18)
                else:
                    break
            create_room = Room.objects.create(sender_user=sender_user, receiver_user=receiver_user, room_name=new_room)
            room_name = create_room.room_name
        
        return redirect('room', room_name=room_name)




class ChatRoom(LoginRequiredMixin, View):
    queryset = Room.objects.all()

    def get(self, request, room_name, *args, **kwargs):
        room = get_object_or_404(Room, room_name=room_name)
        sender = request.user.id
        sender_name = User.objects.get(id=sender).username

        # Sets up the user as sender user for chatting
        if room.receiver_user.id == sender:
            receiver = room.sender_user.id
        else:
            receiver = room.receiver_user.id

        # Get all the previous messages from the database
        messages = Message.objects.filter(
            Q(sender_user=sender, receiver_user=receiver) |
            Q(sender_user=receiver, receiver_user=sender)
        ).order_by('timestamp')

        return render(request, 'chat/room.html', {
            'room_name': room_name,
            'sender_id': sender,
            'receiver_id': receiver,
            'messages': messages,
            'sender_name': sender_name
        })