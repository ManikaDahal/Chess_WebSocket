from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from call.models import Invite, ChessRoom
from django.contrib.auth import get_user_model

User = get_user_model()

# Send invite
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_invite(request):
    to_user_id = request.data.get("to_user")
    invite = Invite.objects.create(
        from_user=request.user.id,
        to_user=to_user_id,
        status="pending"
    )
    return Response({"message": "Invite sent", "invite_id": invite.id})

# List pending invites
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pending_invites(request):
    invites = Invite.objects.filter(to_user=request.user.id, status="pending")  # fixed typo
    data = [{"id": i.id, "from_user": i.from_user} for i in invites]
    return Response(data)

# Accept invite
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    invite_id = request.data.get("invite_id")
    invite = Invite.objects.get(id=invite_id)
    invite.status = "accepted"
    invite.save()

    # Create a room
    room = ChessRoom.objects.create(
        player1=invite.from_user,
        player2=invite.to_user,
        current_turn=invite.from_user
    )

    return Response({
        "room_id": room.id,
        "message": "Invite accepted"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_invite(request):
    invite_id = request.data.get("invite_id")
    if not invite_id:
        return Response({"success": False, "error": "invite_id is required"}, status=400)

    try:
        invite = Invite.objects.get(id=invite_id, to_user=request.user, status="pending")
        invite.status = "declined"
        invite.save()
        return Response({"success": True})
    except Invite.DoesNotExist:
        return Response({"success": False, "error": "Invite not found or already handled"}, status=404)
