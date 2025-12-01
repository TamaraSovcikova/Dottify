from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg
from django.utils import timezone 
from datetime import timedelta 

from django.db.models import Q 

from .models import Album, Playlist, Song, DottifyUser
from .forms import AlbumForm, SongForm

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song = self.object     
        
        all_time_avg = song.ratings.aggregate(Avg('stars'))['stars__avg']
        
        # 90-Day Average
        ninety_days_ago_time = timezone.now() - timedelta(days=90)
        recent_avg = song.ratings.filter(created_at__gte=ninety_days_ago_time).aggregate(Avg('stars'))['stars__avg']

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

class AlbumSearchView(ListView):
    model = Album
    template_name = 'dottify/album_search.html'
    context_object_name = 'albums'

    def dispatch(self, request, *args, **kwargs):
        # Authentication Check (Tsince not suing loginrequiredmixin)
        if not request.user.is_authenticated:           
            return HttpResponse('Unauthorized', status=401)        
        
        return super().dispatch(request, *args, **kwargs)

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
    
class AlbumCreateView(LoginRequiredMixin, CreateView):    
    model = Album
    form_class = AlbumForm
    template_name = 'dottify/album_form.html'
   
    def form_valid(self, form):
        # REQUIRED LOGIC -> Automatically set the 'artist_account' field
        # to the DottifyUser profile associated with the current logged-in user.
        
        try:            
            dottify_user = DottifyUser.objects.get(user=self.request.user)
        except DottifyUser.DoesNotExist:           
            # For now, letting know the user is not authorized/set up.
            form.add_error(None, "You do not have an associated Dottify profile to create albums.")
            return self.form_invalid(form)

        form.instance.artist_account = dottify_user      
        return super().form_valid(form)

class AlbumUpdateView(LoginRequiredMixin, UpdateView):
    model = Album 
    form_class = AlbumForm
    template_name = 'dottify/album_form.html'

    # Authorization on GET
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        
        # Skip check if admin admin
        is_admin = user.groups.filter(name='DottifyAdmin').exists()        
        
        if not user.is_authenticated:
            raise Http404("You must be logged in to edit an album.")

        # if Artist AND not the album owner, deny access (403)
        if not is_admin:
            try:                
                album_artist_user = obj.artist_account.user 
                
                if album_artist_user != user:                  
                    return HttpResponseForbidden("You are not authorized to edit this album.")
                    
            except AttributeError:
                # If account or link is missing
                 return HttpResponseForbidden("Album ownership could not be verified.")

        return obj

    # Authorization on POST
    def form_valid(self, form):
        user = self.request.user
        is_admin = user.groups.filter(name='DottifyAdmin').exists()
        
        # Re-verify ownership before saving
        try:
            album_artist_user = self.get_object().artist_account.user
        except AttributeError:
            return HttpResponseForbidden("Album ownership could not be verified during save.")

        if is_admin or album_artist_user == user:         
            return super().form_valid(form)
        else:
            # If authorization failed during POST submission
            return HttpResponseForbidden("You are not authorized to save changes to this album.")

class AlbumDeleteView(LoginRequiredMixin, DeleteView):
    model = Album
    template_name = 'dottify/album_confirm_delete.html'
    
    # successful deletion -> redirect to the homepage.
    success_url = reverse_lazy('home') 

    # override to enforce authorization
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        
        is_admin = user.groups.filter(name='DottifyAdmin').exists()        
        is_owner = False
        try:            
            if obj.artist_account.user == user:
                is_owner = True
        except AttributeError:            
            pass 
     
        if not is_admin and not is_owner:
            return HttpResponseForbidden("You are not authorized to delete this album.")

        # If authorized (Admin OR Owner) proceed
        return obj
    
class SongCreateView(ArtistRequiredMixin, CreateView):
    model = Song
    form_class = SongForm
    template_name = 'dottify/song_form.html'

    success_url = reverse_lazy('home')
    def get_form_kwargs(self):
        """Pass the current user for filtering"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class SongUpdateView(LoginRequiredMixin, UpdateView):
    model = Song
    form_class = SongForm
    template_name = 'dottify/song_form.html'

    # UpdateView uses default success_url so i dont have to define
    
    def get_form_kwargs(self):
        """Pass the current user for filtering"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset) # Tsong being edited
        user = self.request.user
        
        is_admin = user.groups.filter(name='DottifyAdmin').exists()        
        is_owner = False
        try:
            # Song -> Album -> Artist Account -> User
            if obj.album.artist_account.user == user:
                is_owner = True
        except AttributeError:           
            pass 

        if not is_admin and not is_owner:
            return HttpResponseForbidden("You are not authorized to edit this song. You must be the owner of the album it belongs to or a Dottify Admin.")

        return obj
    

class SongDeleteView(LoginRequiredMixin, DeleteView):
    model = Song
    template_name = 'dottify/song_confirm_delete.html'
    success_url = reverse_lazy('home') 

    def get_object(self, queryset=None):
        obj = super().get_object(queryset) 
        user = self.request.user
        
        is_admin = user.groups.filter(name='DottifyAdmin').exists()        
        is_owner = False
        try:
            # ong -> Album -> Artist Account -> User
            if obj.album.artist_account.user == user:
                is_owner = True
        except AttributeError:            
            pass 
        
        if not is_admin and not is_owner:
            return HttpResponseForbidden("You are not authorized to delete this song. You must be the owner of the album it belongs to or a Dottify Admin.")
       
        return obj