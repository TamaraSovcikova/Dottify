from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Album, Song, Playlist, DottifyUser

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

        validators = [
            UniqueTogetherValidator(
                queryset=Album.objects.all(),
                fields=['title', 'artist_name', 'format'],
                message="An album with this title, artist name, and format already exists."
            )
        ]
    
    def get_song_set(self,obj):
        return [song.title for song in obj.tracks.all()]    
    
    def create(self, validated_data):        
        user = self.context['request'].user
        
        try:
            dottify_user = DottifyUser.objects.get(user=user)
        except DottifyUser.DoesNotExist:
            # This should ideally be caught by permissions but is a safety net.
            raise serializers.ValidationError({"artist_account": "No DottifyUser profile found for the logged-in user."})

        # Inject the artist_account into the validated data
        validated_data['artist_account'] = dottify_user
        
        return Album.objects.create(**validated_data)


class SongSerializer(serializers.ModelSerializer):
    #ensuring the position filed in sot provided during creation, but others still should be done automatically 
    class Meta: 
        model = Song
        fields = ['id', 'title', 'length', 'album']
        read_only_fields = ['position']
    
    # Enforce Route 7 security requirement
    def create(self, validated_data):        
        user = self.context['request'].user        
        album = validated_data.get('album')
        
        is_admin = user.groups.filter(name='DottifyAdmin').exists()
        
        if not is_admin:            
            try:
                album_owner_user = album.artist_account.user
            except AttributeError:
                # Album is missing an artist_account link
                raise serializers.ValidationError({"album": "The album ownership cannot be verified."})

            if album_owner_user != user:
                # If the user is not an Admin AND not the owner -> reject
                raise serializers.ValidationError({"album": "You are not authorized to add a song to this album."})
        
        return Song.objects.create(**validated_data)

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
        


