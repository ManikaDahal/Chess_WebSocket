from django.db.models import Count
from django.apps import apps
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatRoom, Message, Notification
from asgiref.sync import sync_to_async
from django.db import transaction

@api_view(['GET'])
def chat_history(request, room_id):
    """Returns the message history for a specific room."""
    User = apps.get_model('chess_python', 'CustomUser')
    try:
        room = ChatRoom.objects.get(id=room_id)
        messages = Message.objects.filter(room=room).order_by('timestamp')
        
        data = [
            {
                "message": msg.text,
                "user_id": msg.sender.id,
                "sender_name": msg.sender.username,
                "room_id": room.id,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
        return Response(data)
    except ChatRoom.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def get_or_create_private_room(request):
    """Gets or creates a private chat room between two users."""
    User = apps.get_model('chess_python', 'CustomUser')
    user1_id = request.data.get('user1_id')
    user2_id = request.data.get('user2_id')
    
    if not user1_id or not user2_id:
        return Response({"error": "user1_id and user2_id are required"}, status=400)
    
    try:
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)
        
        # Determine the set of users to look for
        target_users = {user1, user2}
        target_count = len(target_users) # 1 if self-chat, 2 if separate users
        
        # Find a room that contains exactly these users and NO others
        # We filter for rooms that have user1 AND user2, then check if total count matches
        rooms = ChatRoom.objects.filter(users=user1).filter(users=user2).annotate(u_count=Count('users')).filter(u_count=target_count)
        
        if rooms.exists():
            # If multiple rooms exist (due to previous bugs), pick the oldest one
            room = rooms.order_by('created_at').first()
        else:
            room = ChatRoom.objects.create()
            room.users.add(user1)
            if user1 != user2:
                room.users.add(user2)
            room.save()
            
        return Response({"room_id": room.id})
    except User.DoesNotExist:
        return Response({"error": "One or both users not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
