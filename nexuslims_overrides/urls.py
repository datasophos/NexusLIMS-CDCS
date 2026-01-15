"""
NexusLIMS URL overrides.

These URLs override the default MDCS URLs to use custom NexusLIMS views.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Override the tiles view from mdcs_home
    path('home/tiles', views.tiles, name='core_main_app_homepage_tiles'),
]
