from django.contrib import admin
from .models import *

class SearchAdmin(admin.ModelAdmin):
    search_fields = ["name"]

admin.site.register(Photo, SearchAdmin)
admin.site.register(Page, SearchAdmin)
admin.site.register(Garden, SearchAdmin)
admin.site.register(Shapefile, SearchAdmin)
admin.site.register(Corridor, SearchAdmin)
admin.site.register(Event, SearchAdmin)
admin.site.register(Genus, SearchAdmin)
admin.site.register(Species, SearchAdmin)
admin.site.register(Redlist, SearchAdmin)
