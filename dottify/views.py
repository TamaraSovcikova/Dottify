from django.shortcuts import render
from django.views.generic import DetailView, ListView
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group #
from django.db.models import Q 

from .models import Album, Playlist, Song, DottifyUser

class ArtistRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    # Is user an Artist?
    def test_func(self):
        return self.request.user.groups.filter(name='Artist').exists()
    
class DottifyAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    # Is user a DottifyAdmin?
    def test_func(self):
        return self.request.user.groups.fileter(name='DottifyAdmin').exists()

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

class HomeView(ListView): 
    model = Album
    template_name = 'dottify/home.html'
    context_object_name = 'albums'

    # Controlling all data getting passed to the template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initialize everything to empty in the case of the user not meeting specific criteria
        context['albums'] = Album.objects.none()
        context['playlists'] = Playlist.objects.none()
        context['songs'] = Song.objects.none()
        user = self.request.user
    
        # NOTE: Using raw group checks here instead of mixins, as the HomeView 
        # needs to decide *what* to show based on group, not restrict access.
        is_admin = user.is_authenticated and user.groups.filter(name='DottifyAdmin').exists()
        is_artist = user.is_authenticated and user.groups.filter(name='Artist').exists()

        if user.is_authenticated:        
            try:
                dottify_user = DottifyUser.objects.get(user=user)
            except DottifyUser.DoesNotExist:
            # If lacks a DottifyUser profile, show nothing.
                return context
            
            if is_admin:
                # 1. Admin Logic (All data)
                context['albums'] = Album.objects.all()
                context['playlists'] = Playlist.objects.all()
                context['songs'] = Song.objects.all()
            elif is_artist:
                # 2. Artist Logic (Only own albums)
                context['albums'] = Album.objects.filter(artist_account=dottify_user)
                
            else:
                # 3. General User Logic (Only own playlists)
                context['playlists'] = Playlist.objects.filter(owner=dottify_user)
         
        else:
        # Logic for Anonymous Users (albums and public playlists)
            context['albums'] = Album.objects.all()
            context['playlists'] = Playlist.objects.filter(visibility=Playlist.Visibility.PUBLIC)

class AlbumSearchView(LoginRequiredMixin, ListView):
    model = Album
    template_name = 'dottify/album_search.html'
    context_object_name = 'albums'

    def get_queryset(self):
        # base queryset (all albums)
        queryset = super().get_queryset() 
        
        # getting the query from the parapeter '?q='
        query = self.request.GET.get('q')
        
        if query:
            # 'title__icontains' ORM lookup for case-insensitive containment.
            queryset = queryset.filter(title__icontains=query)
            
        self.query = query
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.query
        return context 