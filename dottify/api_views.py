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

from requests import Response
from rest_framework import viewsets

from dottify import views
from .models import Album, DottifyUser, Song, Playlist
from .serializers import AlbumSerializer, PlaylistSerializer, SongSerializer

# --- Main viewset (/api/albums/ and /api/albums/[id]/) ---
class AlbumViewSet(viewsets.ModelViewSet):  
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer

# --- Nested viewset (/api/albums/[album id]/songs/ and /[song id]/) ---
class NestedSongViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SongSerializer 
    
    def get_queryset(self):
        # drf-nested-routers' should auto pass the parents primary key - kwargs dict - parent_lookup[value]
        #TODO: lab uses a slighly different way, crosscheck which is more correct? 
        return Song.objects.filter(album__pk=self.kwargs['parent_lookup_album__pk'])
    
class SongViewSet(viewsets.ModelViewSet): 
    queryset = Song.objects.all()
    serializer_class = SongSerializer 

class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaylistSerializer
    
    def get_queryset(self):
        # only public ones are returned
        return Playlist.objects.filter(visibility=Playlist.Visibility.PUBLIC)
    
class StatisticsAPIView(views.APIView):
    def get(self, request, format=None):
        
        user_count = DottifyUser.objects.count()
        
        album_count = Album.objects.count()
        
        public_playlist_count = Playlist.objects.filter(
            visibility=Playlist.Visibility.PUBLIC
        ).count()
        
        avg_length_result = Song.objects.aggregate(average_length=Avg('length'))
        song_length_average = avg_length_result.get('average_length')
        
        if song_length_average is not None:        
            song_length_average = float(song_length_average) 
        else:
            song_length_average = 0.0

        data = {
            'user_count': user_count,
            'album_count': album_count,
            'public_playlist_count': public_playlist_count,
            'song_length_average': song_length_average,
        }
        
        return Response(data)