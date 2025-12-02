import data_wizard
from .models import DottifyUser, Album, Song, Playlist, Rating, Comment

data_wizard.register(DottifyUser)
data_wizard.register(Album)
data_wizard.register(Song)
data_wizard.register(Playlist)
data_wizard.register(Rating)
data_wizard.register(Comment)