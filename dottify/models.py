from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import slugify
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