from django.apps import apps
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from .models import ChatRoom, Message

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, room_id):
    """Returns the message history for a specific room."""
    try:
        room = ChatRoom.objects.get(id=room_id)
        messages = Message.objects.filter(room=room).order_by('timestamp')
        
        data = [
            {
                "id": msg.id,
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
@permission_classes([IsAuthenticated])
def get_or_create_private_room(request):
    """Gets or creates a private chat room between two users."""
    User = apps.get_model('chess_python', 'CustomUser')
    
    try:
        user1_id = int(request.data.get('user1_id', 0))
        user2_id = int(request.data.get('user2_id', 0))
    except (TypeError, ValueError):
        return Response({"error": "user1_id and user2_id must be integers"}, status=400)

    if not user1_id or not user2_id:
        return Response({"error": "user1_id and user2_id are required"}, status=400)
    
    try:
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)
        
        target_users = {user1, user2}
        target_count = len(target_users)
        
        rooms = ChatRoom.objects.annotate(u_count=Count('users')).filter(u_count=target_count)
        rooms = rooms.filter(users=user1).filter(users=user2)
        
        if rooms.exists():
            room = rooms.order_by('created_at').first()
            room.users.add(user1, user2)
        else:
            room = ChatRoom.objects.create()
            room.users.add(user1)
            if user1 != user2:
                room.users.add(user2)
            room.save()
            
        return Response({"room_id": int(room.id)})
    except User.DoesNotExist:
        return Response({"error": "One or both users not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
