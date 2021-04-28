from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("maps/", views.maps, name="maps"),
    path("maps/<int:id>/", views.map, name="map"),
    path("geojson/<int:id>/", views.geojson, name="geojson"),
]
