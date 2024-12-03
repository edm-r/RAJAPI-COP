from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from ..models import Discussion, DiscussionGroup
from ..serializers import DiscussionSerializer
from ..permissions import IsGroupMember

class DiscussionViewSet(viewsets.ModelViewSet):
    serializer_class = DiscussionSerializer
    permission_classes = [IsAuthenticated, IsGroupMember]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        group_pk = self.kwargs.get('group_pk')
        return Discussion.objects.filter(
            discussion_group_id=group_pk,
            parent__isnull=True  # Uniquement les discussions principales
        )

    def perform_create(self, serializer):
        group = get_object_or_404(
            DiscussionGroup, 
            id=self.kwargs.get('group_pk')
        )
        serializer.save(
            discussion_group=group,
            sender=self.request.user
        )

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None, group_pk=None, forum_pk=None):
        """Ajouter une réponse à une discussion"""
        parent_discussion = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                discussion_group_id=group_pk,
                sender=request.user,
                parent=parent_discussion
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None, group_pk=None, forum_pk=None):
        """Marquer une discussion comme lue"""
        discussion = self.get_object()
        if discussion.receiver == request.user:
            discussion.status = 'read'
            discussion.save()
            
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def unread(self, request, group_pk=None):
        """Récupérer toutes les discussions non lues"""
        unread_discussions = Discussion.objects.filter(
            discussion_group_id=group_pk,
            receiver=request.user,
            status='unread'
        )
        serializer = self.get_serializer(unread_discussions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def thread(self, request, pk=None, group_pk=None, forum_pk=None):
        """Récupérer toute la discussion avec ses réponses"""
        discussion = self.get_object()
        # Inclure la discussion principale et toutes ses réponses
        thread = Discussion.objects.filter(
            Q(id=discussion.id) | Q(parent=discussion)
        ).order_by('created_at')
        serializer = self.get_serializer(thread, many=True)
        return Response(serializer.data)