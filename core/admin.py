from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from .models import *

class MyAdminSite(AdminSite):
    # Text to put at the end of each page"s <title>.
    site_title = "FCC Admin"

    # Text to put in each page"s <h1> (and above login form).
    site_header = "FCC Admin"

    # Text to put at the top of the admin index page.
    index_title = "FCC"

admin_site = MyAdminSite()

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

class UserAdmin(admin.ModelAdmin):
     list_display = ["username", "email", "first_name", "date_joined", "is_staff", "is_active"]
     list_filter = ["is_staff", "is_active"]
     search_fields = ["username", "email"]

admin_site.register(Photo, SearchAdmin)
admin_site.register(Page, SearchAdmin)
admin_site.register(Garden, GardenAdmin)
admin_site.register(GardenNew, SearchAdmin)
admin_site.register(Document, DocAdmin)
admin_site.register(ReferenceSpace, SearchAdmin)
admin_site.register(Event, SearchAdmin)
admin_site.register(Genus, SearchAdmin)
admin_site.register(Species, SearchAdmin)
admin_site.register(SpeciesFeatures, SearchAdmin)
admin_site.register(Redlist, SearchAdmin)
admin_site.register(VegetationType, VegTypeAdmin)

admin_site.register(User, UserAdmin)
admin_site.register(Group)
