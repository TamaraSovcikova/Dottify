
from django import forms
from .models import Album, Rating, Song, DottifyUser, Comment

# --- Album Form (For Routes 3 and 5) ---
class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = [
            'cover_image', 
            'title', 
            'artist_name', 
            'retail_price', 
            'format', 
            'release_date'
        ]

# --- Song Form (For Routes 7 and 9) ---
class SongForm(forms.ModelForm):
    # Position is auto comp in the model's save method.
    # Song cannot exist without Album  
    class Meta:
        model = Song
        fields = ['album', 'title', 'length']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
    
        #Filters albums based on user’s permissions
        if self.user:
            is_artist = self.user.groups.filter(name='Artist').exists()
            is_admin = self.user.groups.filter(name='DottifyAdmin').exists()

            if is_artist:
                try:
                    dottify_user = DottifyUser.objects.get(user=self.user)
                    self.fields['album'].queryset = Album.objects.filter(artist_account=dottify_user)
                except DottifyUser.DoesNotExist:
                    # If the user is an artist but has no profile, show no albums
                    self.fields['album'].queryset = Album.objects.none()
            
            elif not is_admin:
                # should not be possible but as a fall case
                self.fields['album'].queryset = Album.objects.none()