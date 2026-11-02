"""Url router"""

from django.http import HttpResponse
from django.contrib import admin
from nexuslims_gallery import views as gallery_views
from django.urls import include, path


def _stub_view(request):
    return HttpResponse()


urlpatterns = [
    path("staff-admin/", admin.site.urls),
    path("annotate/", include("nexuslims_annotate.urls")),
    path("gallery/", include("nexuslims_gallery.urls")),
    path("admin/gallery/", gallery_views.gallery_admin, name="nexuslims_gallery_admin"),
    # Stub for core_main_app URL referenced by the annotate template
    path("data/", _stub_view, name="core_main_app_data_detail"),
    path("terms/", _stub_view, name="core_website_app_terms"),
]
