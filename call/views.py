from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatRoom, Message, Notification

@api_view(['GET'])
def chat_list(request):
    user=request.user
    rooms = ChatRoom.objects.filter(users=user)
    last_message= Message.objects.filter(room=room).order_by('-timestamp').first()
    data.append({
        "room_id":room.id,
        "last_message":last_message.text if last_message else "",
        "unread_count":unread_count,
    })
    return Response(data)
