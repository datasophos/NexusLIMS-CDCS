""" Url router
"""
from django.urls import include, path

urlpatterns = [
    path('annotate/', include('nexuslims_annotate.urls')),
]
