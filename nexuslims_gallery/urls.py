from django.urls import path
from . import views

urlpatterns = [
    path("", views.gallery_page, name="nexuslims_gallery_page"),
    path("api/next/", views.api_next, name="nexuslims_gallery_api_next"),
]
