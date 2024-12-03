from django.urls import path, include
from rest_framework_nested import routers
from .views import ForumViewSet, DiscussionGroupViewSet, DiscussionViewSet

# Router principal pour les forums
router = routers.DefaultRouter()
router.register(r'forums', ForumViewSet, basename='forum')

# Router pour les groupes de discussion dans les forums
forums_router = routers.NestedDefaultRouter(router, r'forums', lookup='forum')
forums_router.register(r'groups', DiscussionGroupViewSet, basename='forum-groups')

# Router pour les discussions dans les groupes
groups_router = routers.NestedDefaultRouter(forums_router, r'groups', lookup='group')
groups_router.register(r'discussions', DiscussionViewSet, basename='group-discussions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(forums_router.urls)),
    path('', include(groups_router.urls)),
]
