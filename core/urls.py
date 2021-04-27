from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("photos/", views.photos, name="photos"),
    path("photos/<int:id>/", views.gallery, name="gallery"),
    path("work/projects/", views.projects, name="projects"),
    path("work/publications/", views.publications, name="publications"),
    path("work/talks/", views.talks, name="talks"),
]
