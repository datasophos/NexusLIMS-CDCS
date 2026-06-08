from django.urls import path
from . import views

urlpatterns = [
    path(
        "<str:record_id>/descriptions/",
        views.annotate_descriptions,
        name="nexuslims_annotate_descriptions",
    ),
    path(
        "<str:record_id>/panel/", views.annotate_panel, name="nexuslims_annotate_panel"
    ),
    path("<str:record_id>/rate/", views.annotate_rate, name="nexuslims_annotate_rate"),
    path(
        "<str:record_id>/feature/",
        views.annotate_feature,
        name="nexuslims_annotate_feature",
    ),
    path("<str:record_id>/save/", views.annotate_save, name="nexuslims_annotate_save"),
    path(
        "<str:record_id>/save-one/",
        views.annotate_save_one,
        name="nexuslims_annotate_save_one",
    ),
    path("<str:record_id>/", views.annotate_record, name="nexuslims_annotate_record"),
]
