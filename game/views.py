from django.apps import apps
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import GameInvite, GameMove
from chat.models import ChatRoom
from notifications.utils import notify_user_background
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite(request):
    """Sends a chess game invitation."""
    print(f"DEBUG: send_invite called with data: {request.data}")
    to_user_id = request.data.get('to_user')
    User = apps.get_model('chess_python', 'CustomUser')
    
    try:
        receiver = User.objects.get(id=to_user_id)
        sender = request.user
        
        game_type = request.data.get('game_type', 'chess')
        board_id = request.data.get('board_id')
        
        # For non-friend game invites, we still want a room immediately 
        # to coordinate the game signaling.
        room = None
        if game_type != 'friend':
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
        
        print(f"DEBUG: About to create GameInvite. Room: {room}")
        invite = GameInvite.objects.create(
            sender=sender,
            receiver=receiver,
            room=room,
            status='pending',
            game_type=game_type,
            board_id=board_id
        )

        if game_type == 'friend':
            message = f"{sender.username} invited you to be friends!"
        else:
            game_display_name = "Snake & Ladder" if game_type == 'snake' else "Chess"
            message = f"{sender.username} invited you to play {game_display_name}!"
        
        notify_user_background(
            user_id=receiver.id,
            room_id=room.id if room else None,
            message=message,
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
            "room_id": room.id if room else None
        }, status=201)
        
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in send_invite: {e}")
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    """Accepts a chess game invitation."""
    invite_id = request.data.get('invite_id')
    try:
        invite = GameInvite.objects.get(id=invite_id, receiver=request.user)
        invite.status = 'accepted'
        
        # If it was a friend request without a room, create one now
        if not invite.room:
            sender = invite.sender
            receiver = invite.receiver
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
            
            invite.room = room
        
        invite.save()
        
        # Cleanup: if this is a friend request, also mark any other pending friend request 
        # between these two users as accepted (or just something other than 'pending')
        # to avoid duplicates in the "REQUESTS" list.
        if invite.game_type == 'friend':
            GameInvite.objects.filter(
                sender=invite.receiver,
                receiver=invite.sender,
                game_type='friend',
                status='pending'
            ).update(status='accepted')

        GameMove.objects.filter(room_id=invite.room.id).delete()
        print(f"[GAME] History CLEARED for Room {invite.room.id} on acceptance")
        
        notification_message = f"{request.user.username} accepted your friend request!" if invite.game_type == 'friend' else f"{request.user.username} accepted your invitation!"

        notify_user_background(
            user_id=invite.sender.id,
            room_id=invite.room.id,
            message=notification_message,
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
            "room_id": invite.room.id if invite.room else None
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
            room_id=invite.room.id if invite.room else None,
            message=f"{request.user.username} declined your invitation.",
            sender_id=request.user.id,
            sender_name=request.user.username,
            msg_id=f"decline_{invite.id}",
            notification_type="invite_declined",
            category="invitation",
            extra_data={
                "game_type": invite.game_type,
                "board_id": invite.board_id
            }
        )
        
        return Response({"message": "Invitation declined"})
    except GameInvite.DoesNotExist:
        return Response({"error": "Invitation not found"}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_invite(request):
    """Allows the sender to cancel their own pending invitation."""
    invite_id = request.data.get('invite_id')
    try:
        # Check that the invite exists, is pending, and belongs to the requester
        invite = GameInvite.objects.get(id=invite_id, sender=request.user, status='pending')
        invite.delete()
        
        # Optionally notify the receiver via background (FCM) so they can clear the UI
        # Note: If the receiver is offline, they'll just see the invite is gone next time they fetch
        notify_user_background(
            user_id=invite.receiver.id,
            room_id=invite.room.id if invite.room else None,
            message=f"{request.user.username} cancelled the invitation.",
            sender_id=request.user.id,
            sender_name=request.user.username,
            msg_id=f"cancel_{invite_id}",
            notification_type="invite_cancelled",
            category="invitation",
            extra_data={
                "game_type": invite.game_type,
                "board_id": invite.board_id
            }
        )
        
        return Response({"message": "Invitation cancelled"})
    except GameInvite.DoesNotExist:
        return Response({"error": "Invitation not found or cannot be cancelled"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_invites(request):
    """Lists pending invitations for the user (sent and received) with different expiration thresholds."""
    from django.db.models import Q
    
    now = timezone.now()
    friend_threshold = now - timedelta(days=7)
    game_threshold = now - timedelta(minutes=10)
    
    # Base filter for both sent and received
    # Either it's a 'friend' invite within 7 days, OR a game invite within 10 minutes.
    time_filter = (Q(game_type='friend', created_at__gte=friend_threshold)) | \
                  (~Q(game_type='friend'), Q(created_at__gte=game_threshold))

    # Received invites
    received_invites = GameInvite.objects.filter(
        time_filter,
        receiver=request.user, 
        status='pending'
    ).order_by('-created_at')
    
    # Sent invites
    sent_invites = GameInvite.objects.filter(
        time_filter,
        sender=request.user,
        status='pending'
    ).order_by('-created_at')

    def serialize_invite(invite, is_sent):
        other_user = invite.receiver if is_sent else invite.sender
        return {
            "id": invite.id,
            "sender_id": invite.sender.id,
            "sender_name": invite.sender.username,
            "receiver_id": invite.receiver.id,
            "receiver_name": invite.receiver.username,
            "other_name": other_user.username,
            "room_id": invite.room.id if invite.room else None,
            "game_type": invite.game_type,
            "board_id": invite.board_id,
            "created_at": invite.created_at.isoformat()
        }

    return Response({
        "received": [serialize_invite(i, False) for i in received_invites],
        "sent": [serialize_invite(i, True) for i in sent_invites]
    })
