from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

#TODO: User is week 4 material - make sure to go over it again
class DottifyUser(models.Model):
    # Links to the built-in Django User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dottify_profile' 
    )

    display_name = models.CharField(max_length=800,unique=True, null=False, blank=False)

    def __str__(self):
        return self.display_name

# Helper function for Albums release date calculation
def get_max_release_date():    
    # Calculates the date 60*3 180 days (6 months) from today, inclusive
    return timezone.now().date() + timedelta(days=6 * 30)
  
class Album(models.Model):
    
    # --- Choices for Format ---
    class Format(models.TextChoices):
        SINGLE = 'SNGL', 'Single'
        REMASTER = 'RMST', 'Remaster'
        DELUXE = 'DLUX', 'Deluxe Edition'
        COMPILATION = 'COMP', 'Compilation'
        LIVE_RECORDING = 'LIVE', 'Live Recording'

    cover_image = models.ImageField(default='no_cover.jpg', blank=True, null=True) #blank=True gives the option of empty fields
    title = models.CharField(max_length=800)
    artist_name = models.CharField(max_length=800)
    
    # Optional link 
    artist_account = models.ForeignKey(
        DottifyUser, 
        on_delete=models.SET_NULL, # If the user is deleted, keep the album but set account to NULL
        null=True, 
        blank=True
    )
    retail_price = models.DecimalField(
        max_digits=5, # Need 3 digits before the decimal, 2 after (3+2=5)
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(999.99)],
        null=False, 
        blank=False
    )
    format = models.CharField(max_length=4, choices=Format.choices, blank=True, null=True)
    release_date = models.DateField(validators=[MaxValueValidator(limit_value=get_max_release_date)], null=False, blank=False) #TODO: double check if this is correct format
    slug = models.SlugField(null=True, blank=True)
  
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'artist_name', 'format'],
                name='unique_album_by_artist_and_format'
            )
        ]
    
    def save(self, *args, **kwargs):
        # Dynamic slugs are updateable
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

# returns a formatted string combiting the title and artist's name
    def __str__(self):
        return f"{self.title} by {self.artist_name}"

class Song(models.Model):
    title = models.CharField(max_length=800, blank=False, null=False)    
    length = models.PositiveIntegerField(
        validators=[MinValueValidator(10)],
        blank=False,
        null=False
    )
    position = models.PositiveIntegerField(
        null=True, 
        blank=True,
        editable=False # Prevents accidental changes via Admin/forms after creation
    )
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE, #Deleting the albums deletes the songs
        related_name='tracks'
    )

    class Meta:
        constraints = [
            # Song titles must be unique within an album
            models.UniqueConstraint(
                fields=['title', 'album'],
                name='unique_song_title_per_album'
            )
        ]
        ordering = ['album', 'position']

    def save(self, *args, **kwargs):
        """
        Overrides save to compute the position automatically only when the song is first added.
        """
        # Check if the object is new (has no ID) AND the position is not yet set
        if not self.id and self.position is None:
            # highest existing position for songs in this album
            last_song = Song.objects.filter(album=self.album).order_by('-position').first()
            
            # Update the position
            if last_song and last_song.position is not None:
                self.position = last_song.position + 1
            else:
                self.position = 1
            
        super().save(*args, **kwargs)

class Playlist(models.Model):

    class Visibility(models.IntegerChoices):
        HIDDEN = 0, 'Hidden'  # Default value
        UNLISTED = 1, 'Unlisted'
        PUBLIC = 2, 'Public'

    name = models.CharField(null=False,blank=False)
    created_at = models.DateTimeField(
        auto_now_add=True, # Automatically set the date/time when created
        editable=False      # Prevents modification 
    )
    songs = models.ManyToManyField(
        'Song',
        related_name='playlists'
    )
    visibility = models.IntegerField(
        choices=Visibility.choices,
        default=Visibility.HIDDEN,
        blank=False,
        null=False
    )    
    owner = models.ForeignKey(
        DottifyUser,
        on_delete=models.CASCADE, # If the owner is deleted, the playlist should be deleted
        related_name='playlists',
        blank=False,
        null=False
    )

    def __str__(self):
        # Displays the name and the owner for clarity
        return f"{self.name} (Owner: {self.owner.display_name})"


def validate_half_step(value):
    """Ensures a Decimal value is a multiple of 0.5."""
    # Check if the value multiplied by 2 is an integer (e.g., 2.5 * 2 = 5.0)
    if (value * 2) % 1 != 0:
        raise ValidationError(
            _('%(value)s is not a valid rating. Ratings must be in 0.5 increments (e.g., 1.5, 2.0).'),
            params={'value': value},
        )

class Rating(models.Model):
    stars = models.DecimalField(
        max_digits=2, # Allows numbers up to 9.9. Must be at least 2 for X.Y.
        decimal_places=1, 
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0),
            validate_half_step # unsure if this is what they meant by only in increments 
        ],
    )        
    def __str__(self):
        return f"Rating: {self.stars}"

class Comment(models.Model):
    comment_text = models.CharField(
        max_length=800,
        blank=False,
        null=False
    )
    
    def __str__(self):
        # Shows a snippet of the comment text if too long
        return self.comment_text[:50] + "..." if len(self.comment_text) > 50 else self.comment_text