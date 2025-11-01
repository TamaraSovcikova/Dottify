from rest_framework import serializers
from .models import Album, Song

'''
Three main serializers will be needed: 
- Song serializer -> position field must be hidden
- Album Serializer -> artist_account must be hidden, n songs displayed as list of titles
- Playlist serializer -> is read-only, with two requirements ; disply_name, and list songs are hyperlinks

'''

class AlbumSerializer(serializers.ModelSerializer): 
    #Albums songs required to be listed as strings
    song_set = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            'id','cover_image','title','artist_name', 'retail_price', 'format', 'release_date', 'slug', 'song_set'
        ]
        # artist_account left seperate since it must not be visisble or set via this route
        read_only_fields = ['artist_account']
    
    def get_song_set(self,obj):
        return [song.title for song in obj.tracks.all()]
    
 

