from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Forum, DiscussionGroup, DiscussionMember, Discussion

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class DiscussionSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    receiver_details = UserSerializer(source='receiver', read_only=True)
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Discussion
        fields = [
            'id', 'message', 'sender', 'sender_details', 
            'receiver', 'receiver_details', 'parent',
            'created_at', 'status', 'replies', 'reply_count'
        ]
        read_only_fields = ['sender', 'created_at', 'status']

    def get_replies(self, obj):
        """Récupère les réponses directes à cette discussion"""
        replies = obj.replies.all()[:3]  # Limite aux 3 dernières réponses
        return DiscussionSerializer(replies, many=True).data

    def get_reply_count(self, obj):
        """Compte le nombre total de réponses"""
        return obj.replies.count()

class DiscussionMemberSerializer(serializers.ModelSerializer):
    member_details = UserSerializer(source='member', read_only=True)

    class Meta:
        model = DiscussionMember
        fields = ['id', 'member', 'member_details', 'joined_at']
        read_only_fields = ['joined_at']

class DiscussionGroupSerializer(serializers.ModelSerializer):
    creator_details = UserSerializer(source='created_by', read_only=True)
    members_count = serializers.SerializerMethodField()
    latest_discussions = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionGroup
        fields = [
            'id', 'theme', 'created_by', 'creator_details',
            'status', 'visibility', 'created_at', 'updated_at',
            'members_count', 'latest_discussions', 'is_member'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_members_count(self, obj):
        return obj.members.count()

    def get_latest_discussions(self, obj):
        latest = obj.discussions.filter(parent__isnull=True).order_by('-created_at')[:3]
        return DiscussionSerializer(latest, many=True).data

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(member=request.user).exists()
        return False

class ForumSerializer(serializers.ModelSerializer):
    creator_details = UserSerializer(source='created_by', read_only=True)
    groups_count = serializers.SerializerMethodField()
    latest_group = serializers.SerializerMethodField()

    class Meta:
        model = Forum
        fields = [
            'id', 'title', 'description', 'category',
            'created_by', 'creator_details', 'status',
            'created_at', 'updated_at', 'groups_count',
            'latest_group'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_groups_count(self, obj):
        return obj.discussion_groups.count()

    def get_latest_group(self, obj):
        latest = obj.discussion_groups.order_by('-created_at').first()
        if latest:
            return DiscussionGroupSerializer(latest).data
        return None

class ForumDetailSerializer(ForumSerializer):
    groups = serializers.SerializerMethodField()

    class Meta(ForumSerializer.Meta):
        fields = ForumSerializer.Meta.fields + ['groups']

    def get_groups(self, obj):
        groups = obj.discussion_groups.filter(visibility='public')
        return DiscussionGroupSerializer(
            groups, 
            many=True,
            context=self.context
        ).data