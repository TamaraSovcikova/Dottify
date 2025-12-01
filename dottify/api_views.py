# Use this file for your API viewsets only

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions

from .models import Album, DottifyUser, Song, Playlist
from .serializers import AlbumSerializer, PlaylistSerializer, SongSerializer
from django.db.models import Avg


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the owner (Album's artist_account) or 
    a DottifyAdmin to edit or delete the Album object.
    """

    def has_object_permission(self, request, view, obj):
        # Allow (GET, HEAD, OPTIONS) for viewing by anyone
        if request.method in permissions.SAFE_METHODS:
            return True        
        
        if not request.user.is_authenticated:
            return False
            
        is_admin = request.user.groups.filter(name='DottifyAdmin').exists()
        if is_admin:
            return True
        
        # (PUT/PATCH/DELETE) are only allowed to the owner.
        # Check if obj.artist_account is set and its linked User matches request.user
        if obj.artist_account and obj.artist_account.user == request.user:
            return True

        return False

# --- Main viewset (/api/albums/ and /api/albums/[id]/) ---
class AlbumViewSet(viewsets.ModelViewSet):  
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer

# --- Nested viewset (/api/albums/[album id]/songs/ and /[song id]/) ---
class NestedSongViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SongSerializer 
    
    def get_queryset(self):
       

        # drf-nested-routers' should auto pass the parents primary key - kwargs dict - parent_lookup[value]
        return Song.objects.filter(album__pk=self.kwargs['album_pk'])
    
class SongViewSet(viewsets.ModelViewSet): 
    queryset = Song.objects.all()
    serializer_class = SongSerializer 

class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaylistSerializer
    queryset = Playlist.objects.all()
    
    def get_queryset(self):
        # only public ones are returned
        return Playlist.objects.filter(visibility=Playlist.Visibility.PUBLIC)
    
class StatisticsAPIView(APIView):
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