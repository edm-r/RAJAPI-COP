from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.forms.models import model_to_dict
from django.db import transaction
from datetime import date, datetime

from .models import (
    Project, ProjectMember, Task, 
    ProjectDocument, ProjectVersion
)
from .serializers import (
    ProjectDetailSerializer, ProjectListSerializer,
    ProjectMemberSerializer, TaskSerializer, 
    ProjectDocumentSerializer, ProjectVersionSerializer,
    ProjectUpdateSerializer
)
from .permissions import IsProjectOwner, IsProjectMember, HasProjectRole

def json_serial(obj):
    """Fonction d'aide pour sérialiser les dates dans JSON"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

class VersionControlMixin:
    def _create_version(self, project, previous_state, changes, user):
        """Méthode utilitaire pour créer une nouvelle version"""
        latest_version = ProjectVersion.objects.filter(project=project).order_by('-version_number').first()
        version_number = 1 if not latest_version else latest_version.version_number + 1
        
        # Conversion des dates en strings pour le stockage JSON
        for field, value in previous_state.items():
            if isinstance(value, (date, datetime)):
                previous_state[field] = value.isoformat()
        
        return ProjectVersion.objects.create(
            project=project,
            version_number=version_number,
            modified_by=user,
            changes=changes,
            previous_state=previous_state
        )

    def _get_changes(self, old_data, new_data):
        """Méthode utilitaire pour détecter les changements"""
        changes = {}
        for field, new_value in new_data.items():
            if field in old_data and old_data[field] != new_value:
                old_val = old_data[field].isoformat() if isinstance(old_data[field], (date, datetime)) else old_data[field]
                new_val = new_value.isoformat() if isinstance(new_value, (date, datetime)) else new_value
                
                changes[field] = {
                    'old': old_val,
                    'new': new_val
                }
        return changes
    
class ProjectViewSet(VersionControlMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasProjectRole]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'location']
    search_fields = ['title', 'description', 'objectives', 'reference_number']
    ordering_fields = ['created_at', 'deadline', 'start_date', 'status']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Project.objects.all()
        return Project.objects.filter(members__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        if self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectDetailSerializer

    def create(self, request, *args, **kwargs):
        """Crée un nouveau projet"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            project = serializer.save(owner=self.request.user)
            
            # Créer le membre propriétaire
            ProjectMember.objects.create(
                project=project,
                user=self.request.user,
                role='owner',
                joined_at=timezone.now().date()
            )

            # Créer la première version
            self._create_version(
                project=project,
                previous_state={},
                changes={"action": "project_created"},
                user=request.user
            )

        response_data = {
            "message": "Projet créé avec succès",
            "reference_number": project.reference_number,
            "project": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Met à jour un projet existant"""
        instance = self.get_object()
        current_state = model_to_dict(instance)
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        changes = self._get_changes(current_state, serializer.validated_data)
        
        with transaction.atomic():
            project = serializer.save()
            if changes:
                self._create_version(
                    project=project,
                    previous_state=current_state,
                    changes=changes,
                    user=request.user
                )

        response_data = {
            "message": "Projet mis à jour avec succès",
            "project": ProjectDetailSerializer(project).data,
            "changes": changes
        }
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Crée une nouvelle version du projet"""
        project = self.get_object()
        current_state = model_to_dict(project)

        serializer = ProjectUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        changes = self._get_changes(current_state, serializer.validated_data)
        
        if not changes:
            return Response(
                {"error": "Aucun changement détecté"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for field, value in serializer.validated_data.items():
                setattr(project, field, value)
            project.save()

            version = self._create_version(
                project=project,
                previous_state=current_state,
                changes=changes,
                user=request.user
            )

        return Response({
            "message": "Nouvelle version créée avec succès",
            "version": ProjectVersionSerializer(version).data,
            "project": ProjectDetailSerializer(project).data,
            "changes": changes
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Liste toutes les versions d'un projet"""
        project = self.get_object()
        versions = ProjectVersion.objects.filter(project=project)
        serializer = ProjectVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore_version(self, request, pk=None):
        """Restaure une version spécifique du projet"""
        project = self.get_object()
        version_number = request.data.get('version_number')
        
        try:
            version = ProjectVersion.objects.get(project=project, version_number=version_number)
        except ProjectVersion.DoesNotExist:
            return Response(
                {"error": f"Version {version_number} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            current_state = model_to_dict(project)
            
            # Restaurer les champs en excluant les relations et champs spéciaux
            exclude_fields = ['id', 'created_at', 'updated_at', 'owner']
            for field, value in version.previous_state.items():
                if hasattr(project, field) and field not in exclude_fields:
                    if isinstance(value, str) and field in ['start_date', 'deadline']:
                        try:
                            value = datetime.fromisoformat(value).date()
                        except (ValueError, TypeError):
                            continue
                    setattr(project, field, value)
            
            project.save()

            # Créer une version pour la restauration
            self._create_version(
                project=project,
                previous_state=current_state,
                changes={
                    "action": "version_restored",
                    "restored_from_version": version_number,
                    "restored_at": timezone.now().isoformat()
                },
                user=request.user
            )

        return Response({
            "message": f"Projet restauré à la version {version_number}",
            "project": ProjectDetailSerializer(project).data
        })

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Liste les membres du projet"""
        project = self.get_object()
        members = project.members.all()
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        
        if not IsProjectOwner().has_object_permission(request, self, project):
            return Response(
                {"error": "Seul le propriétaire peut ajouter des membres"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ProjectMemberSerializer(data=request.data)
        if serializer.is_valid():
            if ProjectMember.objects.filter(
                project=project,
                user=serializer.validated_data['user']
            ).exists():
                return Response(
                    {"error": "L'utilisateur est déjà membre du projet"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            member = serializer.save(
                project=project,
                joined_at=timezone.now().date()
            )

            return Response({
                "message": "Membre ajouté avec succès",
                "member": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        project = self.get_object()
        
        if not IsProjectOwner().has_object_permission(request, self, project):
            return Response(
                {"error": "Seul le propriétaire peut retirer des membres"},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"error": "L'ID de l'utilisateur est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = ProjectMember.objects.get(project=project, user_id=user_id)
            if member.role == 'owner':
                return Response(
                    {"error": "Impossible de retirer le propriétaire du projet"},
                    status=status.HTTP_400_BAD_WARNING
                )

            # Sauvegarder les informations du membre avant suppression
            member_info = ProjectMemberSerializer(member).data
            member.delete()

            return Response({
                "message": "Membre retiré avec succès"
            }, status=status.HTTP_204_NO_CONTENT)
        except ProjectMember.DoesNotExist:
            return Response(
                {"error": "Membre non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
    @action(detail=True, methods=['post'])
    def upload_documents(self, request, pk=None):
        """Upload un ou plusieurs documents pour un projet"""
        project = self.get_object()
        if not IsProjectMember().has_object_permission(request, self, project):
            return Response(
                {"error": "Seuls les membres du projet peuvent uploader des documents"},
                status=status.HTTP_403_FORBIDDEN
            )

        files = request.FILES.getlist('documents')
        if not files:
            return Response(
                {"error": "Aucun document fourni"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_documents = []
        for file in files:
            doc = ProjectDocument.objects.create(
                project=project,
                document=file,
                uploaded_by=request.user,
                title=request.data.get('title', file.name),
                description=request.data.get('description', '')
            )
            created_documents.append(doc)

        # Créer une version pour l'ajout de documents
        current_state = model_to_dict(project)
        changes = {
            "documents_added": [doc.title for doc in created_documents]
        }
        self._create_version(
            project=project,
            previous_state=current_state,
            changes=changes,
            user=request.user
        )

        serializer = ProjectDocumentSerializer(created_documents, many=True)
        return Response({
            "message": f"{len(files)} document(s) uploadé(s) avec succès",
            "documents": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Liste tous les documents d'un projet"""
        project = self.get_object()
        documents = project.documents.all()
        serializer = ProjectDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def remove_document(self, request, pk=None):
        """Supprime un document du projet"""
        project = self.get_object()
        document_id = request.query_params.get('document_id')
        
        if not document_id:
            return Response(
                {"error": "ID du document requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document = ProjectDocument.objects.get(id=document_id, project=project)
            document_title = document.title
            document.delete()

            # Créer une version pour la suppression du document
            current_state = model_to_dict(project)
            changes = {
                "document_removed": document_title
            }
            self._create_version(
                project=project,
                previous_state=current_state,
                changes=changes,
                user=request.user
            )

            return Response({
                "message": "Document supprimé avec succès"
            })
        except ProjectDocument.DoesNotExist:
            return Response(
                {"error": "Document non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )

class TaskViewSet(VersionControlMixin, viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'assigned_to']
    ordering_fields = ['due_date', 'created_at']

    def get_queryset(self):
        return Task.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        task = serializer.save(
            project=project,
            assigned_by=self.request.user
        )

        # Créer une version pour l'ajout de la tâche
        current_state = model_to_dict(project)
        changes = {
            "task_added": {
                "title": task.title,
                "assigned_to": task.assigned_to.get_full_name() if task.assigned_to else None
            }
        }
        self._create_version(
            project=project,
            previous_state=current_state,
            changes=changes,
            user=self.request.user
        )

        return task

class ProjectDocumentViewSet(VersionControlMixin, viewsets.ModelViewSet):
    serializer_class = ProjectDocumentSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return ProjectDocument.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        serializer.save(
            project=project,
            uploaded_by=self.request.user
        )