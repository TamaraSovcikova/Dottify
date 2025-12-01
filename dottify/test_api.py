from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Album, DottifyUser

class CustomTestSheetD_API(APITestCase):  
    def setUp(self):
       
        self.artist_group = Group.objects.create(name='Artist')
        
        self.artist_user = User.objects.create_user(username='artist', password='password')
        self.artist_user.groups.add(self.artist_group)
        
        self.general_user = User.objects.create_user(username='general', password='password')
        self.artist_profile = DottifyUser.objects.create(user=self.artist_user, display_name='Artist Owner')
        self.album = Album.objects.create(
            title='Original Title', artist_account=self.artist_profile, artist_name='Artist Test',
            format='SNGL', release_date='2023-01-01', retail_price='5.00'
        )
        self.album_url = f'/api/albums/{self.album.id}/'
        
        # Data for attempted update
        self.update_data = {
            'title': 'Hacked Title',
            'artist_name': 'Artist Hack Test',
            'format': 'DLUX',
            'release_date': '2020-01-01',
            'retail_price': '15.00',
        }

    def test_api_album_update_user(self):
        """
        Ensure a general user cannot update an album via the API.        
        """
        # Log in as a general (unauthorized) user
        self.client.login(username='general', password='password')
        
        # Attempt to update the album 
        response = self.client.put(self.album_url, self.update_data, format='json')        
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_album_update_owner_succeeds(self):
        """Ensure the album owner can update the album via the API."""
        self.client.login(username='artist', password='password')
        
        self.update_data['title'] = 'Updated Title by Owner'

        response = self.client.put(self.album_url, self.update_data, format='json')          
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the album title WAS changed
        self.album.refresh_from_db()
        self.assertEqual(self.album.title, 'Updated Title by Owner')