from django.http import HttpResponseForbidden
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Avg
from django.utils import timezone 
from datetime import timedelta 
from .models import Album, Playlist, Song, DottifyUser
from .forms import AlbumForm, SongForm

class ArtistOrAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Checks if the user is authenticated and belongs to either the 'Artist' 
    or the 'DottifyAdmin' group.
    """
    def test_func(self):
        user = self.request.user
        is_artist = user.groups.filter(name='Artist').exists()
        is_admin = user.groups.filter(name='DottifyAdmin').exists()
        return is_artist or is_admin

class ArtistRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='Artist').exists()
    
class DottifyAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='DottifyAdmin').exists()
    
# --- Custom Mixin for Authorization ---
class ContentOwnerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check if the user is a DottifyAdmin or the owner of the content.    
    """
    def get_owner_user(self):
        """
        Must be overridden by the subclass to return the User object         
        """
        raise ImproperlyConfigured(
            f"{self.__class__.__name__} is missing the implementation of get_owner_user()."
        )

    def test_func(self):
        user = self.request.user
        
        # 1. Admin Check
        is_admin = user.groups.filter(name='DottifyAdmin').exists()
        if is_admin:
            return True # Admins always pass

        # 2. Owner Check
        try:
            owner_user = self.get_owner_user()
            return owner_user == user
        except Exception:            
            return False
    
    def handle_no_permission(self):        
        if self.request.user.is_authenticated:            
            return HttpResponseForbidden("You do not have permission to view or modify this content.")
        
        # If not authenticated, use default LoginRequiredMixin
        return super().handle_no_permission()

class AlbumDetailView(DetailView):
    model = Album
    template_name = 'dottify/album_detail.html'
    context_object_name = 'album'
    
    # Required slug redirection/URL check
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        required_slug = self.object.slug
        current_slug = kwargs.get('slug')
            
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song = self.object     
        
        all_time_avg = song.rating_set.aggregate(Avg('stars'))['stars__avg']
        
        # 90-Day Average
        ninety_days_ago_time = timezone.now() - timedelta(days=90)
        recent_avg = song.rating_set.filter(created_at__gte=ninety_days_ago_time).aggregate(Avg('stars'))['stars__avg']

        # format N.N or 'N.A'
        def format_rating(avg_value):
            if avg_value is not None:                
                return f"{avg_value:.1f}" # one decimal place
            return "N.A"

        context['all_time_rating'] = format_rating(all_time_avg)
        context['recent_rating'] = format_rating(recent_avg)
        
        return context

class UserDetailView(DetailView):
    model = DottifyUser
    template_name = 'dottify/user_detail.html'
    context_object_name = 'dottify_user'
     
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Required canonical slug        
        required_slug = self.object.display_name.lower().replace(' ', '-')        
        current_slug = kwargs.get('slug') 
        
        if current_slug != required_slug or current_slug is None:            
            return redirect(
                reverse(
                    'user_detail', 
                    kwargs={
                        'pk': self.object.pk, 
                        'slug': required_slug
                    }
                ),                
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
        
        albums_qs = Album.objects.none()
        playlists_qs = Playlist.objects.none()
        songs_qs = Song.objects.none() 

        user = self.request.user

        is_admin = user.is_authenticated and user.groups.filter(name='DottifyAdmin').exists()
        is_artist = user.is_authenticated and user.groups.filter(name='Artist').exists()

        if user.is_authenticated:            
            dottify_user = DottifyUser.objects.get(user=user)            

            if is_admin:
                # 1. Admin Logic (All data)
                albums_qs = Album.objects.all()
                playlists_qs = Playlist.objects.all()
                songs_qs = Song.objects.all()
            elif is_artist:
                # 2. Artist Logic (Only own albums)
                albums_qs = Album.objects.filter(artist_account=dottify_user)
            else:
                # 3. General User Logic (Only own playlists)
                playlists_qs = Playlist.objects.filter(owner=dottify_user)
        else:
            # 4. Logic for Anonymous Users (albums and public playlists)
            albums_qs = Album.objects.all()
            playlists_qs = Playlist.objects.filter(visibility=Playlist.Visibility.PUBLIC)

        context['albums'] = albums_qs
        context['playlists'] = playlists_qs
        context['songs'] = songs_qs
              
        total_count = albums_qs.count() 
        # Total results found: N' requirement.
        context['total_results_found'] = total_count
        return context


class AlbumSearchView(LoginRequiredMixin, ListView):
    model = Album
    template_name = 'dottify/album_search.html'
    context_object_name = 'albums'    

    def get_queryset(self):
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
        context['total_results_found'] = context['albums'].count()
        return context 
    
class AlbumCreateView(ArtistOrAdminRequiredMixin, CreateView):    
    model = Album
    form_class = AlbumForm
    template_name = 'dottify/album_form.html'
   
    def form_valid(self, form):
        # REQUIRED LOGIC -> Automatically set the 'artist_account' field        
        
        try:            
            dottify_user = DottifyUser.objects.get(user=self.request.user)
        except DottifyUser.DoesNotExist:           
            form.add_error(None, "You do not have an associated Dottify profile to create albums.")
            return self.form_invalid(form)

        form.instance.artist_account = dottify_user      
        return super().form_valid(form)
    
    def get_success_url(self):        
        # Reverse to generate the URL for the album detail page.
        return reverse('album_detail', kwargs={
            'pk': self.object.pk,  
            'slug': self.object.slug 
        })

class AlbumUpdateView(ContentOwnerOrAdminMixin, UpdateView):
    model = Album 
    form_class = AlbumForm
    template_name = 'dottify/album_form.html'

    # Implementation required by ContentOwnerOrAdminMixin
    def get_owner_user(self):
        album = self.get_object() 
        return album.artist_account.user

    # Authorization on POST
    def form_valid(self, form):       
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('album_detail', kwargs={
            'pk': self.object.pk,
            'slug': self.object.slug
        })

class AlbumDeleteView(ContentOwnerOrAdminMixin, DeleteView):
    model = Album
    template_name = 'dottify/album_confirm_delete.html'
    
    # successful deletion -> redirect to the homepage.
    success_url = reverse_lazy('home') 

    # Implementation required by ContentOwnerOrAdminMixin
    def get_owner_user(self):
        album = self.get_object() 
        return album.artist_account.user
    
class SongCreateView(ArtistOrAdminRequiredMixin, CreateView):
    model = Song
    form_class = SongForm
    template_name = 'dottify/song_form.html'

    success_url = reverse_lazy('home')
    def get_form_kwargs(self):
        """Pass the current user for filtering"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        user = self.request.user
        selected_album = form.cleaned_data.get('album')
        
        # --- Post Authorization Check (Route 7) ---
        if user.groups.filter(name='Artist').exists():            
            try:
                dottify_user = DottifyUser.objects.get(user=user)
            except DottifyUser.DoesNotExist:                
                return HttpResponseForbidden("User profile not found. Cannot create songs.")
            
            if selected_album.artist_account != dottify_user:                
                return HttpResponseForbidden("You can only create songs for your own albums.")
            
        # If the user is an Admin, or is a matching Artist, proceed
        return super().form_valid(form)

class SongUpdateView(ContentOwnerOrAdminMixin, UpdateView):
    model = Song
    form_class = SongForm
    template_name = 'dottify/song_form.html'    
    
    def get_form_kwargs(self):
        """Pass the current user for filtering"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    # Implementation required by ContentOwnerOrAdminMixin
    def get_owner_user(self):
        song = self.get_object() 
        return song.album.artist_account.user
    
    def get_success_url(self):        
        return reverse('song_detail', kwargs={'pk': self.object.pk})
    

class SongDeleteView(ContentOwnerOrAdminMixin, DeleteView):
    model = Song
    template_name = 'dottify/song_confirm_delete.html'
    success_url = reverse_lazy('home') 

    # Implementation required by ContentOwnerOrAdminMixin
    def get_owner_user(self):
        song = self.get_object() 
        return song.album.artist_account.user