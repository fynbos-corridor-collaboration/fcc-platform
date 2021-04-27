from django.contrib import admin
from .models import *

class SearchAdmin(admin.ModelAdmin):
    search_fields = ["name"]

admin.site.register(Photo, SearchAdmin)
