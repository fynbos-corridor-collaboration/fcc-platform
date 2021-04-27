from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.conf import settings
from django.http import HttpResponse
import urllib.request, json 
from django.contrib import messages
from django.utils.safestring import mark_safe

def index(request):
    context = {}
    return render(request, "core/index.html", context)

def photos(request):
    category = None
    context = {
        "header": { "title": "Photos", "subtitle": "Some photo galleries" },
        "categories": PhotoCategory.objects.all(),
        "category": category if category else 1,
    }
    return render(request, "core/photos.galleries.html", context)

def gallery(request, id):
    info = get_object_or_404(PhotoGallery, pk=id)
    context = {
        "header": { "title": info, "subtitle": mark_safe("<a href='../'><i class='fa fa-arrow-left'></i> Back to overview</a>") },
        "info": info,
    }
    return render(request, "core/photos.gallery.html", context)

def projects(request):
    projects = Project.objects.all()
    context = {
        "header": { "title": "Projects", "subtitle": "An overview of the main projects I have worked on over the years" },
        "projects": projects,
    }
    return render(request, "core/projects.html", context)

def publications(request):
    publications = Publication.objects.all()
    context = {
        "header": { "title": "Publications", "subtitle": "An overview of the main publications I have worked on over the years" },
        "publications": publications,
    }
    return render(request, "core/publications.html", context)

def talks(request):
    talks = Presentation.objects.all()
    context = {
        "header": { "title": "Talks", "subtitle": "An overview of the main publications I have worked on over the years" },
        "talks": talks,
    }
    return render(request, "core/talks.html", context)

