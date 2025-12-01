from rest_framework import serializers
from .models import Album, Song, Playlist

class AlbumSerializer(serializers.ModelSerializer): 
    #Albums songs required to be listed as strings
    song_set = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            'id','cover_image','title','artist_name', 'retail_price', 'format', 'release_date', 'slug', 'song_set'
        ]
        # artist_account left seperate since it must not be visisble or set via this route
        read_only_fields = ['artist_account', 'slug']
    
    def get_song_set(self,obj):
        return [song.title for song in obj.tracks.all()]    


class SongSerializer(serializers.ModelSerializer):
    #ensuring the position filed in sot provided during creation, but others still should be done automatically 
    class Meta: 
        model = Song
        fields = ['id', 'title', 'length', 'album']
        read_only_fields = ['position']

class PlaylistSerializer(serializers.ModelSerializer):

    owner = serializers.CharField(source='owner.display_name', read_only=True)

    songs = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='song-detail' #automatically router generated
    )

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'created_at', 'visibility', 'owner', 'songs']
        read_only_fields = fields
        


