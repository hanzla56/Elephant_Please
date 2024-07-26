import json
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from .models import Mychats
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Exists


User = get_user_model()


@login_required
def index(request):
    frnd_name = request.GET.get('user', None)
    mychats_data = None

    if frnd_name:
        if User.objects.filter(username=frnd_name).exists():
            frnd_ = User.objects.get(username=frnd_name)
            if Mychats.objects.filter(me=request.user, frnd=frnd_).exists():
                mychats_data = Mychats.objects.get(me=request.user, frnd=frnd_).chats

    # Filter friends who have chats with the current user
    friends_with_chats = User.objects.exclude(pk=request.user.id).filter(
        Exists(
            Mychats.objects.filter(me=request.user, frnd=OuterRef('pk')) |
            Mychats.objects.filter(me=OuterRef('pk'), frnd=request.user)
        )
    )

    # Prepare the last messages for each chat
    last_messages = {}
    for friend in friends_with_chats:
        my_chat = Mychats.objects.filter(me=request.user, frnd=friend).first()
        frnd_chat = Mychats.objects.filter(me=friend, frnd=request.user).first()
        chat = my_chat or frnd_chat

        if chat and chat.chats:
            try:
                chat_data = json.loads(chat.chats)
                last_message = max(chat_data, key=lambda msg: msg['timestamp'])
                last_messages[friend.username] = last_message['message']
            except (ValueError, TypeError, KeyError) as e:
                print(f"Error processing chat data for {friend.username}: {e}")

    # Set default friend if no friend is specified
    if not frnd_name and friends_with_chats.exists():
        frnd_ = friends_with_chats.first()
        if Mychats.objects.filter(me=request.user, frnd=frnd_).exists():
            mychats_data = Mychats.objects.get(me=request.user, frnd=frnd_).chats
            frnd_name = frnd_.username

    return render(request, 'chat/index.html', {
        'my': mychats_data,
        'chats': mychats_data,
        'frnds': friends_with_chats,
        'last_messages': last_messages,
        'default_user': frnd_name
    })
    
    
    

# @login_required
# def index(request):
#     frnd_name = request.GET.get('user', None)
#     mychats_data = None

#     if frnd_name:
#         if User.objects.filter(username=frnd_name).exists():
#             frnd_ = User.objects.get(username=frnd_name)
#             if Mychats.objects.filter(me=request.user, frnd=frnd_).exists():
#                 mychats_data = Mychats.objects.get(me=request.user, frnd=frnd_).chats

#     # Filter friends who have chats with the current user
#     friends_with_chats = User.objects.exclude(pk=request.user.id).filter(
#         Exists(
#             Mychats.objects.filter(me=request.user, frnd=OuterRef('pk')) |
#             Mychats.objects.filter(me=OuterRef('pk'), frnd=request.user)
#         )
#     )

#     # Prepare the last messages for each chat
#     last_messages = {}
#     for friend in friends_with_chats:
#         my_chat = Mychats.objects.filter(me=request.user, frnd=friend).first()
#         frnd_chat = Mychats.objects.filter(me=friend, frnd=request.user).first()
#         chat = my_chat or frnd_chat

#         if chat and chat.chats:
#             try:
#                 chat_data = json.loads(chat.chats)
#                 last_message = max(chat_data, key=lambda msg: msg['timestamp'])
#                 last_messages[friend.username] = last_message['message']
#             except (ValueError, TypeError, KeyError) as e:
#                 print(f"Error processing chat data for {friend.username}: {e}")

#     return render(request, 'chat/index.html', {
#         'my': mychats_data,
#         'chats': mychats_data,
#         'frnds': friends_with_chats,
#         'last_messages': last_messages,
#     })
    
    
    
    