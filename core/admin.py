from django.contrib import admin
from .models import *

class SearchAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    exclude = ["content_html"]

class VegTypeAdmin(admin.ModelAdmin):
    autocomplete_fields = ["spaces"]

class DocAdmin(SearchAdmin):
    list_display = ["name", "author", "active"]

class GardenAdmin(SearchAdmin):
    list_display = ["name", "active"]
    list_filter = ["active", "organizations"]

admin.site.register(Photo, SearchAdmin)
admin.site.register(Page, SearchAdmin)
admin.site.register(Garden, GardenAdmin)
admin.site.register(Document, DocAdmin)
admin.site.register(ReferenceSpace, SearchAdmin)
admin.site.register(Corridor, SearchAdmin)
admin.site.register(Event, SearchAdmin)
admin.site.register(Genus, SearchAdmin)
admin.site.register(Species, SearchAdmin)
admin.site.register(Redlist, SearchAdmin)
admin.site.register(VegetationType, VegTypeAdmin)
