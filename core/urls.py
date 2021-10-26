from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("gardens/", views.gardens, name="gardens"),
    path("gardens/map/", views.gardens_map, name="gardens_map"),
    path("gardens/<int:id>/", views.garden, name="garden"),
    path("gardens/<int:garden>/photos/", views.photos, name="garden_photos"),
    path("gardens/<int:id>/edit/", views.garden_form, name="garden_form"),
    path("gardens/create/", views.garden_form, name="garden_form"),
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

    path("about/our-organisations/", views.organizations, name="organizations"),
    path("about/<slug:slug>/", views.page, name="about"),
    path("join/<slug:slug>/", views.page, name="join"),
    path("resources/<slug:slug>/", views.page, name="resources"),
    path("page/<slug:slug>/", views.page, name="page"),

    path("fynbos-rehabilitation/", views.page, {"slug": "fynbos-rehabilitation"}),
    path("fynbos-rehabilitation/site-selection/", views.report, {"site_selection": True}, name="rehabilitation_site_selection"),
    path("fynbos-rehabilitation/site-selection/map/", views.report, {"show_map": True, "site_selection": True}, name="rehabilitation_site_selection_map"),
    path("fynbos-rehabilitation/site-selection/how-this-works/", views.page, {"slug": "site-selection-how-this-works"}, name="site_selection_how_this_works"),
    path("fynbos-rehabilitation/site-selection/<str:lat>/<str:lng>/", views.report, {"site_selection": True}, name="rehabilitation_site_selection"),
    path("fynbos-rehabilitation/assessment/", views.rehabilitation_assessment, name="rehabilitation_assessment"),
    path("fynbos-rehabilitation/design/", views.rehabilitation_design, name="rehabilitation_design"),
    path("fynbos-rehabilitation/work-plan/", views.rehabilitation_workplan, name="rehabilitation_workplan"),
    path("fynbos-rehabilitation/monitoring/", views.rehabilitation_monitoring, name="rehabilitation_monitoring"),
    path("fynbos-rehabilitation/plant-selection/", views.profile, name="rehabilitation_plant_selection"),

    path("maps/update/", views.update_map),
    path("corridors/", views.corridors, name="corridors"),
    path("corridors/overview/", views.corridors_overview, name="corridors_overview"),
    path("corridors/rivers/", views.corridors_rivers, name="corridors_rivers"),
    path("corridors/rivers/methodology/", views.corridors_rivers_methodology, name="corridors_rivers_methodology"),
    path("corridors/rivers/<int:id>/", views.corridor_rivers, name="corridor_rivers"),

    path("newsletter/", views.newsletter, name="newsletter"),
]
