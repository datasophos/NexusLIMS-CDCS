"""Url router"""

from django.http import HttpResponse
from django.urls import include, path


def _stub_view(request):
    return HttpResponse()


urlpatterns = [
    path("annotate/", include("nexuslims_annotate.urls")),
    path("gallery/", include("nexuslims_gallery.urls")),
    # Stub for core_main_app URL referenced by the annotate template
    path("data/", _stub_view, name="core_main_app_data_detail"),
    path("terms/", _stub_view, name="core_website_app_terms"),
]
