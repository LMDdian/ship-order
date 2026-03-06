from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Message
from .serializers import MessageSerializer


class MessageListView(APIView):
    """当前用户的消息列表，GET 按创建时间倒序"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Message.objects.filter(user=request.user).order_by("-created_at")
        serializer = MessageSerializer(qs, many=True)
        return Response(serializer.data)


class MessageUnreadCountView(APIView):
    """当前用户未读消息数量，用于红点展示"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Message.objects.filter(user=request.user, looked=False).count()
        return Response({"count": count})


class MessageDetailView(APIView):
    """单条消息详情，PATCH 可标记为已读"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        msg = Message.objects.filter(user=request.user, pk=pk).first()
        if not msg:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = MessageSerializer(msg)
        return Response(serializer.data)

    def patch(self, request, pk: int):
        msg = Message.objects.filter(user=request.user, pk=pk).first()
        if not msg:
            return Response(status=status.HTTP_404_NOT_FOUND)
        looked = request.data.get("looked")
        if looked is True:
            msg.looked = True
            msg.save(update_fields=["looked"])
        serializer = MessageSerializer(msg)
        return Response(serializer.data)
