from django.db import models
from django.conf import settings

class Forum(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived')
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='created_forums'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class DiscussionGroup(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived')
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private')
    ]

    theme = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    visibility = models.CharField(
        max_length=20, 
        choices=VISIBILITY_CHOICES, 
        default='public'
    )
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name='discussion_groups'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.theme} - {self.forum.title}"

class DiscussionMember(models.Model):
    discussion_group = models.ForeignKey(
        DiscussionGroup,
        on_delete=models.CASCADE,
        related_name='members'
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussion_memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['discussion_group', 'member']

    def __str__(self):
        return f"{self.member.username} - {self.discussion_group.theme}"

class Discussion(models.Model):
    STATUS_CHOICES = [
        ('read', 'Read'),
        ('unread', 'Unread')
    ]

    discussion_group = models.ForeignKey(
        DiscussionGroup,
        on_delete=models.CASCADE,
        related_name='discussions'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_discussions'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_discussions',
        null=True,
        blank=True
    )
    message = models.TextField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='unread'
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Discussion in {self.discussion_group.theme} by {self.sender.username}"