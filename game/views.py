from django.apps import apps
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import GameInvite, GameMove
from chat.models import ChatRoom
from notifications.utils import notify_user_background
from django.db.models import Count

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite(request):
    """Sends a chess game invitation."""
    to_user_id = request.data.get('to_user')
    User = apps.get_model('chess_python', 'CustomUser')
    
    try:
        receiver = User.objects.get(id=to_user_id)
        sender = request.user
        
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

        game_type = request.data.get('game_type', 'chess')
        board_id = request.data.get('board_id')

        invite = GameInvite.objects.create(
            sender=sender,
            receiver=receiver,
            room=room,
            status='pending',
            game_type=game_type,
            board_id=board_id
        )

        game_display_name = "Snake & Ladder" if game_type == 'snake' else "Chess"
        
        notify_user_background(
            user_id=receiver.id,
            room_id=room.id,
            message=f"{sender.username} invited you to play {game_display_name}!",
            sender_id=sender.id,
            sender_name=sender.username,
            msg_id=f"invite_{invite.id}",
            notification_type=f"{game_type}_invite",
            category="invitation",
            extra_data={
                "board_id": board_id,
                "game_type": game_type
            }
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
        
        GameMove.objects.filter(room_id=invite.room.id).delete()
        print(f"[GAME] History CLEARED for Room {invite.room.id} on acceptance")
        
        notify_user_background(
            user_id=invite.sender.id,
            room_id=invite.room.id,
            message=f"{request.user.username} accepted your invitation!",
            sender_id=request.user.id,
            sender_name=request.user.username,
            msg_id=f"accept_{invite.id}",
            notification_type="invite_accepted",
            category="invitation",
            extra_data={
                "game_type": invite.game_type,
                "board_id": invite.board_id
            }
        )
        
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
        
        notify_user_background(
            user_id=invite.sender.id,
            room_id=invite.room.id,
            message=f"{request.user.username} declined your invitation.",
            sender_id=request.user.id,
            sender_name=request.user.username,
            msg_id=f"decline_{invite.id}",
            notification_type="invite_declined",
            category="invitation"
        )
        
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
            "game_type": invite.game_type,
            "board_id": invite.board_id,
            "created_at": invite.created_at.isoformat()
        }
        for invite in invites
    ]
    return Response(data)
