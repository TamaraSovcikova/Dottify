# Use this file for your API viewsets only
# E.g., from rest_framework import ...

'''
1. Album ViewSet - handling all the primary album routes
        - /api/albums
        - /api/albums/[id] 

2. Song Vewiset - handing all song routes
        - /api/songs
        - /api/songs/[id]

3. Playlist viewset - handling read only playlist routes
        -/api/playlists
        -/api/plalists/[id]
        AND applied the public visibility filter


4. Nested song viewset - which will handle read only nested album song routes
        - /api/albums/[album id]/songs/
        - /api/albums/[album id]/songs/[song id]/

5. Statistics API View - using DRF's apiview and the django orm, it will claculte the require statistics
'''

from rest_framework import viewsets
from .models import Album, Song
from .serializers import AlbumSerializer, SongSerializer

# --- Main viewset (/api/albums/ and /api/albums/[id]/) ---
class AlbumViewSet(viewsets.ModelViewSet):  
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer

# --- Nested viewset (/api/albums/[album id]/songs/ and /[song id]/) ---
# requires song serializer TODO 
class NestedSongViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for songs nested under a specific album.
    """
    serializer_class = SongSerializer 
    
    def get_queryset(self):
        # drf-nested-routers' should auto pass the parents primary key - kwargs dict - parent_lookup[value]
        return Song.objects.filter(album__pk=self.kwargs['parent_lookup_album__pk'])
    
class SongViewSet(viewsets.ModelViewSet): 
    queryset = Song.objects.all()
    serializer_class = SongSerializer 