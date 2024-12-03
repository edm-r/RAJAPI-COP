from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Forum
from ..serializers import ForumSerializer, ForumDetailSerializer
from ..permissions import IsForumAdmin

class ForumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        return Forum.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ForumDetailSerializer
        return ForumSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        forum = self.get_object()
        if not IsForumAdmin().has_permission(request, self):
            return Response(
                {"error": "Permission refusée"},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        if new_status not in dict(Forum.STATUS_CHOICES):
            return Response(
                {"error": "Statut invalide"},
                status=status.HTTP_400_BAD_REQUEST
            )

        forum.status = new_status
        forum.save()
        serializer = self.get_serializer(forum)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        forum = self.get_object()
        return Response({
            'total_groups': forum.discussion_groups.count(),
            'active_groups': forum.discussion_groups.filter(status='active').count(),
            'total_discussions': sum(
                group.discussions.count() 
                for group in forum.discussion_groups.all()
            ),
            'total_members': sum(
                group.members.count() 
                for group in forum.discussion_groups.all()
            )
        })