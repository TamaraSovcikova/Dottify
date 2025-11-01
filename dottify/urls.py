from django.urls import path, include
from rest_framework.routers import DefaultRouter 
from .api_views import (
    AlbumViewSet 
)

'''
will included the routing using the DefulatRoutes and the NestedDefaultRoutes from drf-nested-routers
'''
router = DefaultRouter()
# Route 1 & 2: /api/albums/ and /api/albums/[id]/
router.register(r'albums', AlbumViewSet, basename='album')

urlpatterns = [
    path('api/', include(router.urls)),
]

