from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from ..models import DiscussionGroup, DiscussionMember
from ..serializers import (
    DiscussionGroupSerializer, 
    DiscussionMemberSerializer
)
from ..permissions import IsGroupAdmin, IsGroupMember

class DiscussionGroupViewSet(viewsets.ModelViewSet):
    serializer_class = DiscussionGroupSerializer  # Add this line
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'visibility']
    search_fields = ['theme']

    def get_queryset(self):
        forum_pk = self.kwargs.get('forum_pk')
        queryset = DiscussionGroup.objects.filter(forum_id=forum_pk)
        if not self.request.user.is_staff:
            return queryset.filter(
                visibility='public'
            ) | queryset.filter(
                members__member=self.request.user
            )
        return queryset

    def perform_create(self, serializer):
        forum_pk = self.kwargs.get('forum_pk')
        serializer.save(
            forum_id=forum_pk,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None, forum_pk=None):
        group = self.get_object()
        
        if group.visibility == 'private' and not request.user.is_staff:
            return Response(
                {"error": "Ce groupe est privé"},
                status=status.HTTP_403_FORBIDDEN
            )

        if group.members.filter(member=request.user).exists():
            return Response(
                {"error": "Vous êtes déjà membre de ce groupe"},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = DiscussionMember.objects.create(
            discussion_group=group,
            member=request.user
        )
        
        serializer = DiscussionMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None, forum_pk=None):
        group = self.get_object()
        
        try:
            membership = group.members.get(member=request.user)
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DiscussionMember.DoesNotExist:
            return Response(
                {"error": "Vous n'êtes pas membre de ce groupe"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None, forum_pk=None):
        group = self.get_object()
        members = group.members.all()
        serializer = DiscussionMemberSerializer(members, many=True)
        return Response(serializer.data)