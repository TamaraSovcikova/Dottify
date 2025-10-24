from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

# Create your models here.


class DottifyUser(models.Model):
    # Links to the built-in Django User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dottify_profile' 
    )

    display_name = models.CharField(
        max_length=800, # need to double check the requirement for this later
        unique=True,
        blank=False,
        null=False
    )

    def __str__(self):
        return self.display_name

def get_max_release_date():
    # 6 * 30 days is 180 days. Using timedelta is safest.
    return timezone.now().date() + timedelta(days=6*30)


class Album(models.Model):
    
    # --- 1. Choices for Format ---
    class Format(models.TextChoices):
        SINGLE = 'SNGL', 'Single'
        REMASTER = 'RMST', 'Remaster'
        DELUXE = 'DLUX', 'Deluxe Edition'
        COMPILATION = 'COMP', 'Compilation'
        LIVE_RECORDING = 'LIVE', 'Live Recording'


    # --- 2. Fields & Constraints ---

    # Optional image, uses the default 'no_cover.jpg'. No upload_to set
    cover_image = models.ImageField(
        default='no_cover.jpg',
        blank=True,
        null=True
    )

    title = models.CharField(
        max_length=800,
        blank=False,
        null=False
    )

    artist_name = models.CharField(
        max_length=800,
        blank=False,
        null=False
    )
    
    # Optional link to a DottifyUser (ForeignKey, allows null)
    artist_account = models.ForeignKey(
        'DottifyUser', # String reference is safer for now
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='albums' # for reverse lookup
    )

    format = models.CharField(
        max_length=4,
        choices=Format.choices,
        blank=True,
        null=True
    )

    retail_price = models.DecimalField(
        max_digits=5, # Need 3 digits before the decimal, 2 after (3+2=5)
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(999.99)],
        blank=False,
        null=False
    )
    
    # Release date: required, must be in the past or max 6*30 days in the future
    release_date = models.DateField(
        validators=[MaxValueValidator(get_max_release_date)],
        blank=False,
        null=False
    )

    # Slug field: not unique, but required on save. Must be blank/null on instantiation.
    # TODO : Implement said field
  
    class Meta:        
        unique_together = ['title', 'artist_name', 'format']
        verbose_name_plural = "Albums"

    # TODO: implement save method

    def __str__(self):
        return f"{self.title} by {self.artist_name}"