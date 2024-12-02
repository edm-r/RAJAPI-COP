from rest_framework import serializers
from .models import Project, ProjectMember, ProjectVersion, Task, ProjectDocument
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomDateField(serializers.DateField):
    def to_representation(self, value):
        if value:
            return value.strftime('%Y-%m-%d')
        return None

    def to_internal_value(self, value):
        return super().to_internal_value(value)
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_by_details = UserSerializer(source='assigned_by', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_to', 'assigned_by',
            'due_date', 'status', 'created_at', 'updated_at',
            'assigned_to_details', 'assigned_by_details'
        ]
        read_only_fields = ['created_at', 'updated_at', 'assigned_by']

class ProjectDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = ProjectDocument
        fields = [
            'id', 'title', 'description', 'document', 'document_url',
            'uploaded_by', 'uploaded_at', 'uploaded_by_details'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']

class ProjectDetailSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'reference_number', 'title', 'description', 'objectives',
            'deadline', 'status', 'owner', 'start_date', 'location',
            'created_at', 'updated_at', 'owner_details', 'tasks', 'documents'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at', 'reference_number']

class ProjectListSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)
    reference_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'reference_number', 'title', 'status', 'start_date', 
            'deadline', 'location', 'created_at', 'owner_details'
        ]

class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'objectives', 'deadline',
            'status', 'start_date', 'location'
        ]

class ProjectMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'role', 'joined_at', 'status', 'user_details']
        read_only_fields = ['joined_at']

class ProjectVersionSerializer(serializers.ModelSerializer):
    modified_by_details = UserSerializer(source='modified_by', read_only=True)

    class Meta:
        model = ProjectVersion
        fields = [
            'id', 'version_number', 'modified_by', 'modified_by_details',
            'modified_at', 'changes', 'previous_state'
        ]
        read_only_fields = ['version_number', 'modified_by', 'modified_at']