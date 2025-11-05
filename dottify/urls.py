from django.urls import path, include
from rest_framework_nested import routers
from .api_views import (
    AlbumViewSet,
    NestedSongViewSet,
    SongViewSet,
    PlaylistViewSet,
    StatisticsAPIView
)

'''
will included the routing using the DefulatRoutes and the NestedDefaultRoutes from drf-nested-routers
'''
router = routers.DefaultRouter()

# Basic album router
router.register(r'albums', AlbumViewSet)
# Basic routes 3,4 for songs
router.register(r'songs', SongViewSet)

router.register(r'playlists', PlaylistViewSet)

# Nested router for album -> song relationships
album_router = routers.NestedDefaultRouter(router, r'albums', lookup='album') #attached to the albums resource. lookup specifies the key in the URL. 

# for the album specifi songs /[album_id]/songs and /song_id
album_router.register(r'songs', NestedSongViewSet, basename='album-songs')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(album_router.urls)),
    path('api/statistics/', StatisticsAPIView.as_view(), name='statistics'),
]

