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

def maps(request):
    context = {
        "maps": 
    }


