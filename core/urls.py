from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("gardens/", views.gardens, name="gardens"),
    path("gardens/<int:id>/", views.garden, name="garden"),
    path("gardens/<int:garden>/photos/", views.photos, name="garden_photos"),
    path("maps/", views.maps, name="maps"),
    path("maps/<int:id>/", views.map, name="map"),
    path("space/<int:id>/", views.space, name="space"),
    path("geojson/<int:id>/", views.geojson, name="geojson"),
    path("report/", views.report, name="report"),
    path("report/map/", views.report, {"show_map": True}, name="report_map"),
    path("report/<str:lat>/<str:lng>/", views.report, name="report"),
    path("species/", views.species_overview, name="species"),
    path("species/all/", views.species_full_list, name="species_full_list"),
    path("species/search/", views.species_full_list, name="species_search"),
    path("species/<int:id>/", views.species, name="species"),
    path("species/genus/<int:genus>/", views.species_list, name="genus"),
    path("species/family/<int:family>/", views.species_list, name="family"),
    path("vegetation-types/", views.vegetation_types, name="vegetation_types"),
    path("vegetation-types/<slug:slug>/", views.vegetation_type, name="vegetation_type"),
    path("vegetation-types/<slug:vegetation_type>/species/", views.species_overview, name="vegetation_type_species"),

    path("profile/<str:lat>,<str:lng>/", views.profile, name="profile"),
    path("profile/<str:lat>,<str:lng>/<slug:section>/", views.profile, name="profile"),
    path("profile/<str:lat>,<str:lng>/<slug:section>/<slug:subsection>/", views.profile, name="profile"),

    path("profile/<int:id>/", views.profile, name="profile"),
    path("profile/<int:id>/<slug:section>/", views.profile, name="profile"),

    path("photos/", views.photos, name="photos"),

    path("accounts/login/", views.user_login, name="login"),
    path("accounts/logout/", views.user_logout, name="logout"),

    path("about/<slug:slug>/", views.page, name="about"),
    path("join/<slug:slug>/", views.page, name="join"),
    path("resources/<slug:slug>/", views.page, name="resources"),

    path("fynbos-rehabilitation/", views.page, {"slug": "fynbos-rehabilitation"}),
    path("fynbos-rehabilitation/site-selection/", views.report, {"site_selection": True}, name="rehabilitation_site_selection"),
    path("fynbos-rehabilitation/site-selection/map/", views.report, {"show_map": True, "site_selection": True}, name="rehabilitation_site_selection_map"),
    path("fynbos-rehabilitation/site-selection/<str:lat>/<str:lng>/", views.report, {"site_selection": True}, name="rehabilitation_site_selection"),
    path("fynbos-rehabilitation/assessment/", views.rehabilitation_assessment, name="rehabilitation_assessment"),
    path("fynbos-rehabilitation/design/", views.rehabilitation_assessment, {"title": "Design your garden"}, name="rehabilitation_design"),
    path("fynbos-rehabilitation/work-plan/", views.rehabilitation_assessment, {"title": "Make a work plan"}, name="rehabilitation_workplan"),
    path("fynbos-rehabilitation/monitoring/", views.rehabilitation_assessment, {"title": "Monitor"}, name="rehabilitation_monitoring"),
    path("fynbos-rehabilitation/plant-selection/", views.profile, name="rehabilitation_plant_selection"),

    path("maps/prioritymap/", views.priority_map, name="priority_map"),
    path("maps/update/", views.update_map),
]
