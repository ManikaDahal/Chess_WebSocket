from django.db.models import Count
from django.apps import apps
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatRoom, Message, Notification, GameInvite
from asgiref.sync import sync_to_async
from django.db import transaction
from .notification_utils import notify_user_background
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, room_id):
    """Returns the message history for a specific room."""
    User = apps.get_model('chess_python', 'CustomUser')
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
    
    # 1. Handle potential string/None IDs robustly
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
        
        # Determine the set of users to look for
        target_users = {user1, user2}
        target_count = len(target_users) # 1 if self-chat, 2 if separate users
        
        # 2. Strict lookup: Find rooms that have exactly these users and NO others
        rooms = ChatRoom.objects.annotate(u_count=Count('users')).filter(u_count=target_count)
        rooms = rooms.filter(users=user1).filter(users=user2)
        
        if rooms.exists():
            # If multiple rooms exist (due to previous bugs), pick the oldest one
            room = rooms.order_by('created_at').first()
            # SELF-HEALING: Ensure users are explicitly added to the M2M relation
            # This handles cases where manual DB edits or bugs removed a user
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite(request):
    """Sends a chess game invitation."""
    to_user_id = request.data.get('to_user')
    User = apps.get_model('chess_python', 'CustomUser')
    
    try:
        receiver = User.objects.get(id=to_user_id)
        sender = request.user
        
        # Get or create a private room
        target_users = {sender, receiver}
        target_count = len(target_users)
        rooms = ChatRoom.objects.annotate(u_count=Count('users')).filter(u_count=target_count)
        rooms = rooms.filter(users=sender).filter(users=receiver)
        
        if rooms.exists():
            room = rooms.first()
        else:
            room = ChatRoom.objects.create()
            room.users.add(sender, receiver)
            room.save()

        # Create invitation
        invite = GameInvite.objects.create(
            sender=sender,
            receiver=receiver,
            room=room,
            status='pending'
        )

        # Trigger FCM notification
        notify_user_background(
            user_id=receiver.id,
            room_id=room.id,
            message=f"{sender.username} invited you to play chess!",
            sender_id=sender.id,
            sender_name=sender.username,
            msg_id=f"invite_{invite.id}",
            notification_type="chess_invite"
        )
        
        return Response({
            "message": "Invitation sent",
            "invite_id": invite.id,
            "room_id": room.id
        }, status=201)
        
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    """Accepts a chess game invitation."""
    invite_id = request.data.get('invite_id')
    try:
        invite = GameInvite.objects.get(id=invite_id, receiver=request.user)
        invite.status = 'accepted'
        invite.save()
        
        return Response({
            "message": "Invitation accepted",
            "room_id": invite.room.id
        })
    except GameInvite.DoesNotExist:
        return Response({"error": "Invitation not found"}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_invite(request):
    """Declines a chess game invitation."""
    invite_id = request.data.get('invite_id')
    try:
        invite = GameInvite.objects.get(id=invite_id, receiver=request.user)
        invite.status = 'declined'
        invite.save()
        return Response({"message": "Invitation declined"})
    except GameInvite.DoesNotExist:
        return Response({"error": "Invitation not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_invites(request):
    """Lists pending invitations for the user."""
    invites = GameInvite.objects.filter(receiver=request.user, status='pending')
    data = [
        {
            "id": invite.id,
            "sender_id": invite.sender.id,
            "sender_name": invite.sender.username,
            "room_id": invite.room.id,
            "created_at": invite.created_at.isoformat()
        }
        for invite in invites
    ]
    return Response(data)
