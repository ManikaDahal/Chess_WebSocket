from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import NotificationLog, NotificationPreference, NOTIFICATION_CATEGORIES

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_notification_status(request):
    """Updates the status of a push notification log."""
    message_id = request.data.get('message_id')
    status_val = request.data.get('status') 

    if not message_id or not status_val:
        return Response(
            {"error": "message_id and status are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if status_val not in ['delivered', 'opened', 'closed', 'blocked']:
        return Response(
            {"error": "Invalid status. Must be 'delivered', 'opened', 'closed', or 'blocked'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if message_id == "permission_blocked":
            updated_count = NotificationLog.objects.filter(
                user=request.user,
                status__in=['sent', 'delivered']
            ).update(status='blocked')
            return Response({
                "message": f"Global status updated to blocked for {updated_count} notifications."
            })

        log_entry = NotificationLog.objects.filter(
            Q(message_id=message_id) | 
            Q(message_id__endswith=message_id) |
            Q(user=request.user, data__id=message_id)
        ).first()
            
        if not log_entry:
            return Response({"error": "Notification log not found"}, status=status.HTTP_404_NOT_FOUND)
            
        terminal_states = ['opened', 'closed', 'blocked']
        if log_entry.status in terminal_states and status_val not in terminal_states:
             pass
        else:
            log_entry.status = status_val
            log_entry.save()
            
        return Response({"message": f"Status updated to {status_val}"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_preferences(request):
    """Returns all notification categories with the user's current blocked status."""
    existing = {
        p.category: p.is_blocked
        for p in NotificationPreference.objects.filter(user=request.user)
    }

    data = [
        {
            "category": key,
            "label": label,
            "is_blocked": existing.get(key, False),
        }
        for key, label in NOTIFICATION_CATEGORIES
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_notification_preference(request):
    """Blocks or unblocks a notification category for the authenticated user."""
    category = request.data.get('category')
    is_blocked = request.data.get('is_blocked')

    valid_categories = [key for key, _ in NOTIFICATION_CATEGORIES]
    if category not in valid_categories:
        return Response(
            {"error": f"Invalid category. Must be one of: {valid_categories}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if is_blocked is None:
        return Response(
            {"error": "is_blocked (bool) is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    pref, created = NotificationPreference.objects.get_or_create(
        user=request.user,
        category=category,
        defaults={"is_blocked": bool(is_blocked)},
    )
    if not created:
        pref.is_blocked = bool(is_blocked)
        pref.save()

    action = "blocked" if pref.is_blocked else "unblocked"
    return Response({"message": f"Category '{category}' is now {action}.", "is_blocked": pref.is_blocked})
