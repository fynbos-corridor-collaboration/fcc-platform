from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("maps/", views.maps, name="maps"),
    path("maps/<int:id>/", views.map, name="map"),
    path("space/<int:id>/", views.space, name="space"),
    path("geojson/<int:id>/", views.geojson, name="geojson"),
    path("report/", views.report, name="report"),
    path("species/", views.species_overview, name="species"),
    path("species/all/", views.species_full_list, name="species_full_list"),
    path("species/search/", views.species_full_list, name="species_search"),
    path("species/<int:id>/", views.species, name="species"),
    path("species/genus/<int:genus>/", views.species_list, name="genus"),
    path("species/family/<int:family>/", views.species_list, name="family"),
    path("vegetation-types/", views.vegetation_types, name="vegetation_types"),
    path("vegetation-types/<slug:slug>/", views.vegetation_type, name="vegetation_type"),
]
