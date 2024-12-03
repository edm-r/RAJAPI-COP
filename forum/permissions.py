from rest_framework import permissions

class IsForumAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour les administrateurs du forum.
    """
    def has_permission(self, request, view):
        # Vérifier si l'utilisateur est staff ou superuser
        return request.user.is_staff or request.user.is_superuser

class IsGroupAdmin(permissions.BasePermission):
    """
    Permission pour les administrateurs de groupe.
    Seul le créateur du groupe ou un admin peut modifier/supprimer le groupe.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Vérifier si l'utilisateur est le créateur du groupe ou un admin
        return (obj.created_by == request.user or 
                request.user.is_staff or 
                request.user.is_superuser)

class IsGroupMember(permissions.BasePermission):
    """
    Permission pour les membres du groupe.
    Seuls les membres peuvent voir et participer aux discussions.
    """
    def has_object_permission(self, request, view, obj):
        # Pour les discussions, vérifier le groupe parent
        if hasattr(obj, 'discussion_group'):
            group = obj.discussion_group
        else:
            group = obj

        # Les groupes publics sont accessibles en lecture à tous
        if request.method in permissions.SAFE_METHODS and group.visibility == 'public':
            return True

        # Vérifier si l'utilisateur est membre du groupe
        return (group.members.filter(member=request.user).exists() or
                request.user.is_staff or 
                request.user.is_superuser)

class CanManageDiscussion(permissions.BasePermission):
    """
    Permission pour gérer les discussions.
    Seul l'auteur peut modifier/supprimer sa discussion.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Vérifier si l'utilisateur est l'auteur de la discussion
        return (obj.sender == request.user or 
                request.user.is_staff or 
                request.user.is_superuser)