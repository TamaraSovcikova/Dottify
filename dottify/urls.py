from django.urls import path, include
from rest_framework_nested import routers

from dottify.views import AlbumCreateView, AlbumDeleteView, AlbumDetailView, AlbumSearchView, AlbumUpdateView, HomeView, SongCreateView, SongDetailView, SongUpdateView, UserDetailView
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

    # Route 2,3,5,6 Album search, create, update, delete
    path('albums/search/', AlbumSearchView.as_view(), name='album_search'),
    path('albums/new/', AlbumCreateView.as_view(), name='album_create'),
    path('albums/<int:pk>/edit/', AlbumUpdateView.as_view(), name='album_edit'),
    path('albums/<int:pk>/delete/', AlbumDeleteView.as_view(), name='album_delete'),

    # Route 4: Album Read
    path('albums/<int:pk>/', AlbumDetailView.as_view(), name='album_detail_pk'),
    path('albums/<int:pk>/<slug:slug>/', AlbumDetailView.as_view(), name='album_detail'),

    # Route 8: Song Read Detail
    path('songs/<int:pk>/', SongDetailView.as_view(), name='song_detail'),

    # Route 11: User Detail
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail_pk'),
    path('users/<int:pk>/<slug:slug>/', UserDetailView.as_view(), name='user_detail'),

    # Route 7, 9, 10
    path('songs/new/', SongCreateView.as_view(), name='song_create'),
    path('songs/<int:pk>/edit/', SongUpdateView.as_view(), name='song_edit'),
    path('songs/<int:pk>/delete/', SongDeleteView.as_view(), name='song_delete'), # <-
    
]