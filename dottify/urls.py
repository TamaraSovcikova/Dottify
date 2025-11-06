from django.urls import path, include
from rest_framework_nested import routers

from dottify.views import AlbumDetailView, HomeView, SongDetailView, UserDetailView
from .api_views import (
    AlbumViewSet,
    NestedSongViewSet,
    SongViewSet,
    PlaylistViewSet,
    StatisticsAPIView
)

router = routers.DefaultRouter()

# ---(API Routers and urlpatterns) ---
router.register(r'albums', AlbumViewSet)
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

# --- HTML VIEWS ---
urlpatterns += [
    #Route 1: Home View
    path('', HomeView.as_view(), name='home'),
    # Route 4: Album Read
    path('albums/<int:pk>/', AlbumDetailView.as_view(), name='album_detail_pk'),
    path('albums/<int:pk>/<slug:slug>/', AlbumDetailView.as_view(), name='album_detail'),

    # Route 8: Song Read Detail
    path('songs/<int:pk>/', SongDetailView.as_view(), name='song_detail'),

    # Route 11: User Detail
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail_pk'),
    path('users/<int:pk>/<slug:slug>/', UserDetailView.as_view(), name='user_detail'),
]