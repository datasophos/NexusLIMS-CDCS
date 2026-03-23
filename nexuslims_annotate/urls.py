from django.urls import path
from . import views

urlpatterns = [
    path('<str:record_id>/panel/', views.annotate_panel, name='nexuslims_annotate_panel'),
    path('<str:record_id>/save/', views.annotate_save, name='nexuslims_annotate_save'),
    path('<str:record_id>/', views.annotate_record, name='nexuslims_annotate_record'),
]
