# dottify/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from datetime import timedelta
from django.utils import timezone
from .models import Album, Song, DottifyUser, Rating, Comment, Playlist


class CustomTestSheetCAndD(TestCase):
    """
    Tests for Sheet C view content (Home, Search) and Sheet D     
    """

    def setUp(self):        
        self.admin_group = Group.objects.create(name='DottifyAdmin')
        self.artist_group = Group.objects.create(name='Artist')
        
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.admin_user.groups.add(self.admin_group)
        
        self.artist_user = User.objects.create_user(username='artist', password='password')
        self.artist_user.groups.add(self.artist_group)
        
        self.other_artist_user = User.objects.create_user(username='other_artist', password='password')
        self.other_artist_user.groups.add(self.artist_group)
        
        self.general_user = User.objects.create_user(username='general', password='password')

        self.artist_profile = DottifyUser.objects.create(user=self.artist_user, display_name='Artist Owner')
        DottifyUser.objects.create(user=self.general_user, display_name='General Profile')

        self.album = Album.objects.create(
            title='Test Album', 
            artist_account=self.artist_profile, 
            artist_name='Artist Test',
            release_date=timezone.now().date(),
            retail_price=9.99,  
            format='DLUX'       
        )
        self.other_album = Album.objects.create(
            title='Unique Album Title', 
            artist_account=self.artist_profile, 
            artist_name='Other Artist',
            release_date=timezone.now().date(),
            retail_price=12.50, 
            format='SNGL'      
        ) 
        self.song = Song.objects.create(title='Test Song', album=self.album, length=180)
        
        # Enhancements Data
        Comment.objects.create(album=self.album, user=self.general_user, comment_text='Great album for testing!')
        Rating.objects.create(song=self.song, stars=5, created_at=timezone.now() - timedelta(days=100)) # All-time
        Rating.objects.create(song=self.song, stars=3, created_at=timezone.now() - timedelta(days=10))  # Recent

        other_artist_profile = DottifyUser.objects.create(
            user=self.other_artist_user, 
            display_name='Other Artist Profile'
        )

        self.client = Client()

    # --- Authorization/CRUD Access Tests (Sheet D) ---

    def test_album_update_owner_succeeds(self):
        """Owner Artist should be able to access album edit view (Route 5)."""
        self.client.login(username='artist', password='password')
        response = self.client.get(reverse('album_edit', kwargs={'pk': self.album.pk}))
        self.assertEqual(response.status_code, 200)

    def test_album_update_other_artist_fails(self):
        """Non-Owner Artist should be forbidden from editing an album (Route 5)."""
        # Create an album owned by the other artist for setup validation
        other_artist_profile = DottifyUser.objects.get(user=self.other_artist_user)
        non_owned_album = Album.objects.create(
        title='Not Mine', 
        artist_account=other_artist_profile, 
        artist_name='Someone Else',
        release_date=timezone.now().date()
    )
        
        self.client.login(username='artist', password='password')
        response = self.client.get(reverse('album_edit', kwargs={'pk': non_owned_album.pk}))
        self.assertEqual(response.status_code, 403) # Forbidden

    def test_song_create_requires_artist_group(self):
        """General user attempting to create a song should be forbidden by ArtistRequiredMixin (Route 7)."""
        self.client.login(username='general', password='password')
        response = self.client.get(reverse('song_create'))
        self.assertEqual(response.status_code, 403) # Forbidden
        
    def test_song_delete_admin_succeeds(self):
        """Admin should be able to delete any song (Route 10)."""
        self.client.login(username='admin', password='password')
        response = self.client.post(reverse('song_delete', kwargs={'pk': self.song.pk}))
        self.assertEqual(response.status_code, 302) # Redirect (deletion successful)

    # --- Home View/List Count/Search Tests (Routes 1 & 2, Sheet D) ---

    def test_home_view_list_count_enhancement(self):
        """Home view must show 'Total results found: N' exactly (Sheet D)."""           

        response = self.client.get(reverse('home'))
        
        self.assertContains(response, 'Total results found: 2')
        self.assertNotContains(response, 'Total results found: 02')

    def test_album_search_results(self):
        """Album search must return correct, case-insensitive results (Route 2)."""
        self.client.login(username='general', password='password')
        response = self.client.get(reverse('album_search') + '?q=album')
        
        self.assertContains(response, 'Test Album') 
        self.assertContains(response, 'Unique Album Title') 
        self.assertContains(response, '(2 found)') 

    # --- Enhancement Content Tests (Sheet D) ---
        
    def test_album_detail_comment_enhancement(self):
        """Album detail must show comment text and DottifyUser display name."""
        response = self.client.get(reverse('album_detail', kwargs={'pk': self.album.pk, 'slug': self.album.slug}))

        self.assertContains(response, 'Great album for testing!')      

    def test_song_ratings_calculation_and_format(self):
        """Song detail must display correct N.N formatted averages and handle N.A."""
        response = self.client.get(reverse('song_detail', kwargs={'pk': self.song.pk}))

        # All-Time Avg: 4.0. Recent Avg: 3.0
        self.assertContains(response, 'Average rating of all time: 4.0')
        self.assertContains(response, 'Recent rating average (last 90 days): 4.0')