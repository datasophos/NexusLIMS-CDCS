"""Url router"""

from django.http import HttpResponse
from django.urls import include, path


def _stub_view(request):
    return HttpResponse()


urlpatterns = [
    path("annotate/", include("nexuslims_annotate.urls")),
    # Stub for core_main_app URL referenced by the annotate template
    path("data/", _stub_view, name="core_main_app_data_detail"),
]
