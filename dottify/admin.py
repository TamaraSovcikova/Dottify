from django.contrib import admin
from .models import (DottifyUser, Album, Song, Playlist, Rating, Comment)
# Register your models here.
admin.site.register(DottifyUser)
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(Rating)
admin.site.register(Comment)
