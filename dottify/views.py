from django.shortcuts import render
from django.views.generic import DetailView
from django.shortcuts import redirect
from django.urls import reverse

from .models import Album, Song, DottifyUser


class AlbumDetailView(DetailView):
    model = Album
    template_name = 'dottify/album_detail.html'
    context_object_name = 'album'
    
    # Required slug redirection/URL check
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        required_slug = self.object.slug
        current_slug = kwargs.get('slug')
            
        # If the provided slug is incrrect OR no slug was provided
        if current_slug != required_slug or 'slug' not in kwargs:
            # Redirect to the canonical URL with the correct slug
            return redirect(
                reverse('album_detail', kwargs={'pk': self.object.pk, 'slug': required_slug}),
                permanent=True
            )

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
class SongDetailView(DetailView):
    model = Song
    template_name = 'dottify/song_detail.html'
    context_object_name = 'song'

class UserDetailView(DetailView):
    model = DottifyUser
    template_name = 'dottify/user_detail.html'
    context_object_name = 'dottify_user'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        required_slug = self.object.display_name.lower().replace(' ', '-')
        current_slug = kwargs.get('slug')
        
        # Check for incorrect, redirect to canonical URL like in Album detail
        if current_slug != required_slug or 'slug' not in kwargs:
            return redirect(
                reverse('user_detail', kwargs={'pk': self.object.pk, 'slug': required_slug}),
                permanent=True
            )
            
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)