from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Album, Song, DottifyUser, Comment, Rating


class CustomTestSheetA(TestCase):
    """Tests for the new model methods and constraints (Sheet D)."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pw123')
        self.dottify_user = DottifyUser.objects.create(user=self.user, display_name='TestDisplay')
        self.album = Album.objects.create(title='Test Album', artist_account=self.dottify_user, artist_name='Artist')
        self.song = Song.objects.create(title='Test Song', album=self.album, length=100)

    # --- Comment Model Tests ---
    
    def test_comment_get_user_display_name_method(self):
        """Test that the required DottifyUser display name is retrieved correctly."""
        comment = Comment.objects.create(album=self.album, user=self.user, comment_text='Test')
        self.assertEqual(comment.get_user_display_name(), 'TestDisplay')

    # --- Rating Model Tests ---

    def test_rating_star_min_max_validation(self):
        """Ensure rating stares are strictly between 1 and 5 (inclusive)."""
        
        rating_high = Rating(song=self.song, star=6)
        with self.assertRaises(ValidationError):
            rating_high.full_clean()

        rating_low = Rating(song=self.song, star=0)
        with self.assertRaises(ValidationError):
            rating_low.full_clean()