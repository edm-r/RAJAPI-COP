from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
import uuid

class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('archived', 'Archived')
    ]
    
    reference_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    objectives = models.TextField()
    deadline = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    start_date = models.DateField()
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Format: RJPC-YYYY-XXXXX (RJPC pour RAJAPI-COP)
            year = self.created_at.strftime('%Y') if self.created_at else timezone.now().strftime('%Y')
            unique_id = str(uuid.uuid4().int)[:5]  # Prendre les 5 premiers chiffres
            self.reference_number = f"RJPC-{year}-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number} - {self.title}"

class ProjectDocument(models.Model):
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document = models.FileField(upload_to='project_documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.project.title}"

    @property
    def document_url(self):
        if self.document:
            return self.document.url
        return None

class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('collaborator', 'Collaborator'),
        ('viewer', 'Viewer')
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('invited', 'Invited'),
        ('pending', 'Pending')
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    joined_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')

    class Meta:
        unique_together = ['project', 'user']

class ProjectVersion(models.Model):
    project = models.ForeignKey(
        'Project', 
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_modifications'
    )
    modified_at = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField()  # Stocke les modifications effectuées
    previous_state = models.JSONField()  # Stocke l'état complet avant modification

    class Meta:
        ordering = ['-version_number']
        unique_together = ['project', 'version_number']

    def __str__(self):
        return f"{self.project.reference_number} - Version {self.version_number}"

class Task(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed')
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='assigned_tasks'
    )
    due_date = models.DateField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)