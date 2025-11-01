# Use this file for your API viewsets only
# E.g., from rest_framework import ...

'''
1. Album ViewSet - handling all the primary album routes
        - /api/albums
        - /api/albums/[id] 

2. Song Vewiset - handing all song routes
        - /api/songs
        - /api/songs/[id]

3. Playlist viewset - handling read only playlist routes
        -/api/playlists
        -/api/plalists/[id]
        AND applied the public visibility filter


4. Nested song viewset - which will handle read only nested album song routes
        - /api/albums/[album id]/songs/
        - /api/albums/[album id]/songs/[song id]/

5. Statistics API View - using DRF's apiview and the django orm, it will claculte the require statistics
'''