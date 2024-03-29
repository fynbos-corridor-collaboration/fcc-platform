from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.conf import settings
from django.http import JsonResponse, HttpResponse, Http404
import urllib.request, json 
from django.contrib import messages
from django.utils.safestring import mark_safe
import folium
from folium.plugins import Fullscreen
import random
from django.db.models import Q, Count
from django.contrib.gis import geos
from django.contrib.gis.measure import D
from django.core.paginator import Paginator
from django.forms import modelform_factory

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from dateutil.relativedelta import relativedelta

# These are used so that we can send mail
from django.core.mail import send_mail
from django.template.loader import render_to_string, get_template

# For token generation
import secrets

# Quick debugging, sometimes it's tricky to locate the PRINT in all the Django 
# output in the console, so just using a simply function to highlight it better
def p(text):
    print("----------------------")
    print(text)
    print("----------------------")

# Also defined in context_processor for templates, but we need it sometimes in the Folium map configuration
MAPBOX_API_KEY = "pk.eyJ1IjoiY29tbXVuaXRyZWUiLCJhIjoiY2lzdHZuanl1MDAwODJvcHR1dzU5NHZrbiJ9.0ETJ3fXYJ_biD7R7FiwAEg"
SATELLITE_TILES = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=" + MAPBOX_API_KEY
STREET_TILES = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=" + MAPBOX_API_KEY
LIGHT_TILES = "https://api.mapbox.com/styles/v1/mapbox/light-v10/tiles/{z}/{x}/{y}?access_token=" + MAPBOX_API_KEY

# Some reference spaces/lists we will be using
SUBURBS = ReferenceSpace.objects.filter(source_id=334434)

COLOR_SCHEMES = {
    "moc": ["#144d58","#a6cee3","#33a02c","#b2df8a","#e31a1c","#fb9a99","#ff7f00","#fdbf6f","#6a3d9a","#cab2d6","#b15928","#ffff99"],
    "accent": ["#7fc97f","#beaed4","#fdc086","#ffff99","#386cb0","#f0027f","#bf5b17","#666666"],
    "dark": ["#1b9e77","#d95f02","#7570b3","#e7298a","#66a61e","#e6ab02","#a6761d","#666666"],
    "pastel": ["#fbb4ae","#b3cde3","#ccebc5","#decbe4","#fed9a6","#ffffcc","#e5d8bd","#fddaec","#f2f2f2"],
    "set": ["#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#ffff33","#a65628","#f781bf","#999999"],
    "dozen": ["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"],
    "green": ["#005824", "#238b45", "#41ae76", "#66c2a4", "#99d8c9", "#ccece6", "#e5f5f9", "#f7fcfd"],
    "blue": ["#084594", "#2171b5", "#4292c6", "#6baed6", "#9ecae1", "#c6dbef", "#deebf7","#f7fbff"],
    "purple": ["#3f007d", "#54278f", "#6a51a3", "#807dba", "#9e9ac8", "#bcbddc", "#dadaeb", "#efedf5", "#fcfbfd"],
    "red": ["#7f0000", "#b30000", "#d7301f", "#ef6548", "#fc8d59", "#fdbb84", "#fdd49e", "#fee8c8", "#fff7ec"],
}

def index(request):
    if "photos" in request.GET:
        return None
        import csv
        from django.core.files.uploadedfile import UploadedFile
        from dateutil.parser import parse
        a = Photo.objects.filter(old_id__isnull=False).order_by("-old_id")
        if a:
            max_id = a[0].old_id
        count = 0
        with open(settings.MEDIA_ROOT + "/import/photos.csv", "r", encoding="utf-8-sig") as csvfile:
            contents = csv.DictReader(csvfile)
            for row in contents:
                id = int(row["id"])
                if id > max_id:
                    count += 1
                    folder = row["folder"]
                    file = row["file"]
                    path = settings.MEDIA_ROOT + f"/old/photos/{folder}/{file}/large.jpg"
                    g = Photo.objects.create(
                        description = row["description"],
                        original = row,
                        date = parse(row["created_at"]),
                        upload_date = parse(row["updated_at"]),
                        image = UploadedFile(file=open(path, "rb")),
                        garden_id = row["site_id"] if row["site_id"] else None,
                        old_id = row["id"],
                    )

                if count == 500:
                    return None
        
    if "photo_update" in request.GET:
        return None
        from dateutil.parser import parse
        a = Photo.objects.filter(old_id__isnull=False)
        for each in a:
            each.date = parse(each.original["created_at"])
            each.upload_date = parse(each.original["updated_at"])
            each.save()

    context = {
        "garden": Garden.objects.filter(active=True).order_by("?")[0],
    }
    return render(request, "core/index.html", context)

def map(request, id):
    info = get_object_or_404(Document, pk=id)
    spaces = info.spaces.all()
    features = []
    if info.spaces.all().count() == 1:
        # If this is only associated to a single space then we show that one
        space = info.spaces.all()[0]

    if spaces.count() > 500 and "show_all_spaces" not in request.GET:
        space_count = spaces.count()
        spaces = spaces[:500]

    map = None
    simplify_factor = None
    geom_type = None

    size = 0
    # If the file is larger than 3MB, then we simplify
    if not "show_full" in request.GET:
        if size > 1024*1024*20:
            simplify_factor = 0.05
        elif size > 1024*1024*10:
            simplify_factor = 0.02
        elif size > 1024*1024*5:
            simplify_factor = 0.001

    colors = ["green", "blue", "red", "orange", "brown", "navy", "teal", "purple", "pink", "maroon", "chocolate", "gold", "ivory", "snow"]

    count = 0
    legend = {}
    show_individual_colors = False
    properties = info.get_dataviz
    if "color_type" in properties:
        if properties["color_type"] == "single":
            # One single color for everything on the map
            show_individual_colors = False
        else:
            # Each space has an individual color
            show_individual_colors = True
    else:
        show_individual_colors = True

    if show_individual_colors and "scheme" in properties:
        s = properties["scheme"]
        colors = COLOR_SCHEMES[s]

    for each in spaces:
        geom_type = each.geometry.geom_type
        if simplify_factor:
            geo = each.geometry.simplify(simplify_factor)
        else:
            geo = each.geometry

        url = each.get_absolute_url

        # If we need separate colors we'll itinerate over them one by one
        if show_individual_colors:
            try:
                color = colors[count]
                count += 1
            except:
                color = colors[0]
                count = 0
            legend[color] = each.name
        else:
            color = None

        content = ""
        content = content + f"<a href='{url}'>View details</a>"

        try:
            features.append({
                "type": "Feature",
                "geometry": json.loads(geo.json),
                "properties": {
                    "name": each.name,
                    "id": each.id,
                    "content": content,
                    "color": color if color else "",
                },
            })
        except Exception as e:
            messages.error(request, f"We had an issue reading one of the items which had an invalid geometry ({each}). Error: {str(e)}")

    data = {
        "type":"FeatureCollection",
        "features": features,
        "geom_type": geom_type,
    }

    context = {
        "info": info,
        "load_map": True,
        "load_leaflet_item": True,
        "load_datatables": True,
        "data": data,
        "properties": properties,
        "show_individual_colors": show_individual_colors,
        "colors": colors,
        "features": features,
    }
    return render(request, "core/map.html", context)

def space(request, id):
    info = get_object_or_404(ReferenceSpace, pk=id)
    geo = info.geometry

    if "download" in request.POST:
        response = HttpResponse(geo.geojson, content_type="application/json")
        response["Content-Disposition"] = f"attachment; filename=\"{info.name}.geojson\""
        return response

    map = folium.Map(
        location=[info.geometry.centroid[1], info.geometry.centroid[0]],
        zoom_start=14,
        scrollWheelZoom=False,
        tiles=STREET_TILES,
        attr="Mapbox",
    )

    folium.GeoJson(
        geo.geojson,
        name="geojson",
    ).add_to(map)

    if info.geometry.geom_type != "Point":
        # For a point we want to give some space around it, but polygons should be
        # an exact fit
        map.fit_bounds(map.get_bounds())

    Fullscreen().add_to(map)

    satmap = folium.Map(
        location=[info.geometry.centroid[1], info.geometry.centroid[0]],
        zoom_start=17,
        scrollWheelZoom=False,
        tiles=SATELLITE_TILES,
        attr="Mapbox",
    )

    folium.GeoJson(
        geo.geojson,
        name="geojson",
    ).add_to(satmap)

    if True:
        # For a point we want to give some space around it, but polygons should be
        # an exact fit, and we also want to show the outline of the polygon on the
        # satellite image
        satmap.fit_bounds(map.get_bounds())
        def style_function(feature):
            return {
                "fillOpacity": 0,
                "weight": 4,
            }
        folium.GeoJson(
            info.geometry.geojson,
            name="geojson",
            style_function=style_function,
        ).add_to(satmap)
    Fullscreen().add_to(satmap)

    context = {
        "info": info,
        "map": map._repr_html_(),
        "satmap": satmap._repr_html_(),
        "center": info.geometry.centroid,
    }
    return render(request, "core/space.html", context)


def maps(request):
    types = Document.Type
    parents = []
    hits = {}
    type_list = {}
    getcolors = {}
    relevant_types = [1,2,3,4,5]
    for each in types:
        e = int(each)
        if e in relevant_types:
            parents.append(e)
            hits[e] = []
            type_list[e] = each.label

    documents = Document.objects.filter(active=True, type__in=relevant_types).order_by("type")
    for each in documents:
        t = each.type
        hits[t].append(each)
        getcolors[each.id] = each.color

    for each in parents:
        if not hits[each]:
            parents.remove(each)

    context = {
        "maps": documents,
        "load_map": True,
        "parents": parents,
        "hits": hits,
        "boundaries": ReferenceSpace.objects.get(pk=983170),
        "type_list": type_list,
        "getcolors": getcolors,
        "title": "Maps",
        "icons": {
            1: "leaf",
            2: "draw-square",
            3: "train",
            4: "map-marker",
            5: "info-circle",
        }
    }
    return render(request, "core/maps.html", context)

def report(request, show_map=False, lat=False, lng=False, site_selection=False):

    if show_map and not "lat" in request.GET:
        map = folium.Map(
            location=[-34.070078, 18.571595],
            zoom_start=10,
            scrollWheelZoom=True,
            tiles=STREET_TILES,
            attr="Mapbox",
        )
        context = {
            "load_map": True,
            "site_selection": site_selection,
            "lat": -34.07,
            "lng": 18.57,
        }
        return render(request, "core/report.map.html", context)
    elif not "lat" in request.GET and not lat:
        context = {
            "site_selection": site_selection,
        }
        return render(request, "core/report.start.html", context)

    info = get_object_or_404(ReferenceSpace, pk=988911)
    schools = get_object_or_404(Document, pk=983409)
    cemeteries = get_object_or_404(Document, pk=983426)
    parks = get_object_or_404(Document, pk=983479)
    rivers = get_object_or_404(Document, pk=983382)
    
    railway = get_object_or_404(Document, pk=2)
    centers = get_object_or_404(Document, pk=983491)
    remnants = get_object_or_404(Document, pk=983097)
    gardens = get_object_or_404(Document, pk=1)
    vegetation = get_object_or_404(Document, pk=983172)
    boundaries = ReferenceSpace.objects.get(pk=983170)

    # These are the layers we open by default on the map
    open_these_layers = [schools.id, cemeteries.id, parks.id, rivers.id, railway.id, remnants.id, gardens.id, boundaries.id, centers.id]

    if "lat" in request.GET:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
    else:
        lat = float(lat)
        lng = float(lng)

    if "next" in request.POST:
        response = redirect("rehabilitation_assessment")
        response.set_cookie("lat", lat)
        response.set_cookie("lng", lng)
        return response

    center = geos.Point(x=lng, y=lat, srid=4326)
    center.transform(3857) # Transform Projection to Web Mercator     
    radius = 1000 # Number of meters distance
    circle = center.buffer(radius) 
    circle.transform(4326) # Transform back to WGS84 to create geojson

    try:
        point = geos.Point(x=lng, y=lat)
        veg = vegetation.spaces.get(geometry__intersects=point)
        veg = veg.get_vegetation_type()
    except:
        veg = None

    #parks = parks.spaces.filter(geometry__within=circle)
    #remnants = remnants.spaces.filter(geometry__distance_lte=(center, D(km=3)))

    parks = parks.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    cemeteries = cemeteries.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    schools = schools.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    remnants = remnants.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    gardens = gardens.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    rivers = rivers.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    railway = railway.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))
    centers = centers.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))

    # We want to figure out what the total river and railway length (in m) in the circle is.
    # To do so we need to convert to a coordinate system that measures things in m
    # See: https://gis.stackexchange.com/questions/180776/get-linestring-length-in-meters-python-geodjango
    length = 0
    for each in rivers:
        geom = each.geometry
        geom = geom.intersection(circle)
        geom.transform(3857)
        length += geom.length

    railway_length = 0
    for each in railway:
        geom = each.geometry
        geom = geom.intersection(circle)
        geom.transform(3857)
        railway_length += geom.length

    expansion = {}
    expansion["count"] = schools.count() + cemeteries.count() + parks.count() + centers.count()
    if expansion["count"] <= 1:
        expansion["rating"] = 0
        expansion["label"] = "<span class='badge bg-danger'>poor</span>"
    elif expansion["count"] <= 3:
        expansion["rating"] = 1
        expansion["label"] = "<span class='badge bg-warning'>okay</span>"
    else:
        expansion["rating"] = 2
        expansion["label"] = "<span class='badge bg-success'>great</span>"
    expansion["label"] = mark_safe(expansion["label"])

    connectors = {}
    connectors["count"] = length + railway_length
    if connectors["count"] <= 200:
        connectors["rating"] = 0
        connectors["label"] = "<span class='badge bg-danger'>poor</span>"
    elif connectors["count"] <= 500:
        connectors["rating"] = 1
        connectors["label"] = "<span class='badge bg-warning'>okay</span>"
    else:
        connectors["rating"] = 2
        connectors["label"] = "<span class='badge bg-success'>great</span>"
    connectors["label"] = mark_safe(connectors["label"])

    existing = {}
    existing["count"] = remnants.count() + gardens.count()
    if existing["count"] <= 0:
        existing["rating"] = 0
        existing["label"] = "<span class='badge bg-danger'>poor</span>"
    elif existing["count"] <= 2:
        existing["rating"] = 1
        existing["label"] = "<span class='badge bg-warning'>okay</span>"
    else:
        existing["rating"] = 2
        existing["label"] = "<span class='badge bg-success'>great</span>"
    existing["label"] = mark_safe(existing["label"])

    types = Document.Type
    parents = []
    hits = {}
    type_list = {}
    getcolors = {}
    relevant_types = [1,2,3,4,5]
    for each in types:
        e = int(each)
        if e in relevant_types:
            parents.append(e)
            hits[e] = []
            type_list[e] = each.label

    documents = Document.objects.filter(active=True, include_in_site_analysis=True).order_by("type")
    for each in documents:
        t = each.type
        hits[t].append(each)
        getcolors[each.id] = each.color

    for each in parents:
        if not hits[each]:
            parents.remove(each)

    context = {
        "parks": parks,
        "cemeteries": cemeteries,
        "rivers": rivers,
        "railway": railway,
        "centers": centers,
        "remnants": remnants,
        "gardens": gardens,
        "schools": schools,
        "expansion": expansion,
        "connectors": connectors,
        "existing": existing,
        "veg": veg,
        "center": center,
        "lat": lat,
        "lng": lng,
        "site_selection": site_selection,
        "open_these_layers": open_these_layers,
        "river_length": length,
        "railway_length": railway_length,
        "maps": documents,
        "load_map": True,
        "parents": parents,
        "hits": hits,
        "boundaries": boundaries,
        "type_list": type_list,
        "getcolors": getcolors,
        "title": "Maps",
        "icons": {
            1: "leaf",
            2: "draw-square",
            3: "train",
            4: "map-marker",
            5: "info-circle",
        },
        "properties": {"map_layer_style": "light-v10"},
    }
    return render(request, "core/report.html", context)

def geojson(request, id):
    info = Document.objects.get(pk=id)
    features = []
    spaces = info.spaces.all()
    intersection = False

    if "space" in request.GET:
        spaces = spaces.filter(id=request.GET["space"])

    if "lat" in request.GET and "lng" in request.GET:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
        center = geos.Point(x=lng, y=lat, srid=4326)
        center.transform(3857) # Transform Projection to Web Mercator     
        radius = 1000 # Number of meters distance
        circle = center.buffer(radius) 
        circle.transform(4326) # Transform back to WGS84 to create geojson
        intersection = True
        spaces = spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))

    geom_type = None
    for each in spaces:
        if each.geometry:
            geom = each.geometry
            if intersection:
                geom = each.geometry.intersection(circle)
            url = each.get_absolute_url
            content = ""
            if each.photo:
                content = f"<a class='d-block' href='{url}'><img alt='{each.name}' src='{each.photo.image.thumbnail.url}' /></a><hr>"
            content = content + f"<a href='{url}'>View details</a>"
            content = content + f"<br><a href='/maps/{info.id}'>View source layer: <strong>{info}</strong></a>"
            if not geom_type:
                geom_type = geom.geom_type
            features.append({
                "type": "Feature",
                "geometry": json.loads(geom.json),
                "properties": {
                    "name": each.name,
                    "content": content,
                    "id": each.id,
                },
            })

    data = {
        "type":"FeatureCollection",
        "features": features,
        "geom_type": geom_type,
    }
    return JsonResponse(data)

def species_overview(request, vegetation_type=None):

    samples = Species.objects.values_list("id", flat=True).filter(photo__isnull=False)
    genus = Genus.objects.all()
    families = Family.objects.all()
    species = Species.objects.all()
    veg_types = VegetationType.objects.all().annotate(total=Count("species"))

    if vegetation_type:
        vegetation_type = VegetationType.objects.get(slug=vegetation_type)
        species = species.filter(vegetation_types=vegetation_type)
        samples = samples.filter(vegetation_types=vegetation_type)

        genus = genus.annotate(total=Count("species", filter=Q(species__vegetation_types=vegetation_type))).filter(total__gt=0)
        families = families.annotate(total=Count("species", filter=Q(species__vegetation_types=vegetation_type))).filter(total__gt=0)
        features = SpeciesFeatures.objects.filter(species__vegetation_types=vegetation_type).distinct()
    else:
        genus = genus.annotate(total=Count("species"))
        families = families.annotate(total=Count("species"))
        features = SpeciesFeatures.objects.all()

    try:
        samples = Species.objects.filter(pk__in=random.sample(list(samples), 4))
    except:
        samples = None

    context = {
        "genus": genus,
        "family": families,
        "load_datatables": True,
        "samples": samples,
        "all": species.count(),
        "features": features,
        "vegetation_types": veg_types,
        "vegetation_type": vegetation_type,
        "veg_link": f"?vegetation_type={vegetation_type.id}" if vegetation_type else "",
    }
    return render(request, "core/species.overview.html", context)

def species_list(request, genus=None, family=None):
    species = Species.objects.all()

    if genus:
        genus = get_object_or_404(Genus, pk=genus)
        species = species.filter(genus=genus)
        full_list = Genus.objects.all()
    if family:
        family = get_object_or_404(Family, pk=family)
        species = species.filter(family=family)
        full_list = Family.objects.all()

    vegetation_type = None
    if "vegetation_type" in request.GET:
        vegetation_type = VegetationType.objects.get(pk=request.GET["vegetation_type"])
        species = species.filter(vegetation_types=vegetation_type)

    full_list = full_list.annotate(total=Count("species"))
    context = {
        "load_datatables": True,
        "genus": genus,
        "family": family,
        "species_list": species,
        "full_list": full_list,
    }
    return render(request, "core/species.all.html", context)

def species_full_list(request):
    species = Species.objects.all()

    vegetation_type = None
    if "vegetation_type" in request.GET:
        vegetation_type = VegetationType.objects.get(pk=request.GET["vegetation_type"])
        species = species.filter(vegetation_types=vegetation_type)

    features = None
    if "feature" in request.GET:
        features = SpeciesFeatures.objects.filter(pk__in=request.GET.getlist("feature"))
        if request.GET.get("search") == "all":
            for each in features:
                species = species.filter(features=each)
        else:
            species = species.filter(features__in=features)

    species = species.distinct()

    context = {
        "species_list": species,
        "load_datatables": True,
        "features": features,
        "vegetation_type": vegetation_type,
    }
    return render(request, "core/species.all.html", context)

def rehabilitation_assessment(request, title="Assess and imagine"):
    if "next" in request.POST:
        if title == "Assess and imagine":
            return redirect("rehabilitation_plant_selection")
        elif title == "Design your garden":
            return redirect("rehabilitation_workplan")
        elif title == "Make a work plan":
            return redirect("rehabilitation_monitoring")
    context = {
        "title": title,
        "social": Page.objects.get(slug="social-assessment"),
        "ecological": Page.objects.get(slug="ecological-assessment"),
        "vision": Page.objects.get(slug="vision-and-mission"),
    }
    return render(request, "core/assessment.html", context)

def rehabilitation_design(request):
    context = {
        "info": Page.objects.get(slug="design-your-garden"),
    }
    return render(request, "core/design.html", context)

def rehabilitation_workplan(request):
    context = {
        "info": Page.objects.get(slug="workplan"),
    }
    return render(request, "core/workplan.html", context)

def rehabilitation_monitoring(request):
    context = {
        "info": Page.objects.get(slug="monitoring"),
    }
    return render(request, "core/monitoring.html", context)

def rehabilitation_plant_selection(request):
    context = {
    }
    return render(request, "core/assessment.html", context)

def species(request, id):
    context = {
        "info": get_object_or_404(Species, pk=id),
    }
    return render(request, "core/species.html", context)

def gardens(request):
    gardens = Garden.objects.prefetch_related("organizations").filter(active=True)
    inactive_gardens = None
    if request.user.is_authenticated:
        inactive_gardens = Garden.objects_unfiltered.filter(active=False)
    context = {
        "all": gardens,
        "page": Page.objects.get(pk=2),
        "load_map": True,
        "load_datatables": True,
        "inactive_gardens": inactive_gardens,
    }
    return render(request, "core/gardens.html", context)

def garden(request, id):
    info = Garden.objects_unfiltered.get(pk=id)
    show_garden = True

    if not info.active:
        show_garden = False
        if request.user.is_authenticated:
            show_garden = True
            if "activate" in request.POST:
                info.active = True
                info.save()
                messages.success(request, "Garden has been activated.")
                return redirect(reverse("garden", args=[info.id]))
        elif "uuid" in request.GET and request.GET.get("uuid") == str(info.uuid):
            show_garden = True

    if request.user.is_staff:
        if "delete" in request.POST:
            info.delete()
            messages.success(request, "The garden was removed.")
            return redirect("gardens")

    if not show_garden:
        raise Http404("This garden was not found.")

    try:
        photos = Photo.objects.filter(garden=info).exclude(id=info.photo.id).order_by("-date")[:12]
    except:
        photos = None

    if info.geometry:
        map = folium.Map(
            zoom_start=14,
            scrollWheelZoom=False,
            location=[info.geometry.centroid[1],info.geometry.centroid[0]],
            tiles=STREET_TILES,
            attr="Mapbox",
        )

        folium.GeoJson(
            info.geometry.geojson,
            name="geojson",
        ).add_to(map)

        Fullscreen().add_to(map)

    context = {
        "map": map._repr_html_() if info.geometry else None,
        "info": info,
        "photos": photos,
    }
    return render(request, "core/garden.html", context)

def garden_form(request, id=None, token=None, uuid=None):

    info = None
    new_garden = True
    if id:
        if not request.user.is_authenticated:
            messages.warning(request, "You must be logged in to access that page.")
            return redirect("index")
        new_garden = False
        ModelForm = modelform_factory(Garden, fields=["name", "content", "phase_assessment", "phase_alienremoval", "phase_landscaping", "phase_pioneers", "phase_birdsinsects", "phase_specialists", "phase_placemaking", "organizations"])
        info = Garden.objects_unfiltered.get(pk=id)
        form = ModelForm(request.POST or None, instance=info)
    elif uuid:
        manager = GardenManager.objects.filter(garden__uuid=uuid, token=token)
        if not manager.exists():
            messages.error(request, "The link is invalid. Please select a garden and re-request a link or contact us if in doubt.")
            return redirect("gardens")
        elif manager[0].token_expiration_date < timezone.now():
            messages.error(request, "The link has expired. Please re-request a link a new below contact us if in doubt.")
            return redirect("garden_manager", manager[0].garden.id)
        else:
            info = manager[0].garden
            new_garden = False
            ModelForm = modelform_factory(Garden, fields=["name", "content", "phase_assessment", "phase_alienremoval", "phase_landscaping", "phase_pioneers", "phase_birdsinsects", "phase_specialists", "phase_placemaking"])
            form = ModelForm(request.POST or None, instance=info)
    else:
        labels = {
            "name": "Garden name",
            "content": "Description",
        }
        ModelForm = modelform_factory(Garden, fields=["name", "content", "phase_assessment", "phase_alienremoval", "phase_landscaping", "phase_pioneers", "phase_birdsinsects", "phase_specialists", "phase_placemaking"], labels=labels)
        form = ModelForm(request.POST or None)

    if request.method == "POST":
        if "photographer" in request.POST:
            Photo.objects.create(
                description = request.POST.get("description"),
                author = request.POST.get("photographer"),
                image = request.FILES.get("photo"),
                garden = info,
            )
            messages.success(request, "The new photo has been added.")
            return redirect(request.get_full_path())
        elif form.is_valid():
            info = form.save()
            if request.POST.get("lat") and request.POST.get("lng"):
                try:
                    lat = float(request.POST.get("lat"))
                    lng = float(request.POST.get("lng"))
                    info.geometry = geos.Point(lng, lat)
                except:
                    pass
                info.save()
            if new_garden:
                info.active = False
                info.source_id = 8
                info.original = request.POST
                info.save()

                mailcontext = {
                    "info": info,
                    "uploader": request.POST.get("your_name"),
                    "email": request.POST.get("email"),
                    "phone": request.POST.get("phone"),
                    "link": reverse("garden", args=[info.id]) + "?uuid=" + str(info.uuid),
                }
                msg_html = render_to_string("mailbody/newgarden.html", mailcontext)
                msg_plain = render_to_string("mailbody/newgarden.txt", mailcontext)

                sender = '"Fynbos Corridor Collaboration Website" <info@fynboscorridors.org>'
                recipient = sender

                send_mail(
                    "New garden added: " + info.name,
                    msg_plain,
                    sender,
                    [recipient],
                    html_message=msg_html,
                )

                messages.success(request, "Thanks! We have received your garden details. We will review this and get back to you (might take a week or so, please stay tuned).")
                return redirect("index")
            else:

                if uuid:
                    mailcontext = {
                        "info": info,
                        "manager": manager[0],
                    }
                    msg_html = render_to_string("mailbody/gardenupdate.html", mailcontext)
                    msg_plain = render_to_string("mailbody/gardenupdate.txt", mailcontext)

                    sender = '"Fynbos Corridor Collaboration Website" <info@fynboscorridors.org>'
                    recipient = sender

                    send_mail(
                        "Garden updated: " + info.name,
                        msg_plain,
                        sender,
                        [recipient],
                        html_message=msg_html,
                    )

                messages.success(request, "Information was saved.")
                return redirect(info.get_absolute_url)
        else:
            messages.error(request, "We could not save your form, please fill out all fields")
    context = {
        "info": info,
        "form": form,
    }
    return render(request, "core/garden.form.html", context)

def garden_manager(request, id):
    info = Garden.objects.get(pk=id)
    if "email" in request.POST:
        email = request.POST.get("email").lower().strip()
        manager = info.managers.filter(email=email)
        if manager:
            manager = manager[0]
            token = secrets.token_urlsafe()
            manager.token = token
            manager.token_expiration_date = timezone.now() + relativedelta(days=30)
            manager.save()
            link = reverse("garden_form", args=[info.uuid, token])
            link = request.build_absolute_uri(link)

            mailcontext = {
                "name": manager.name,
                "garden": info.name,
                "link": link,
            }
            msg_html = render_to_string("mailbody/managegarden.html", mailcontext)
            msg_plain = render_to_string("mailbody/managegarden.txt", mailcontext)

            sender = '"Fynbos Corridor Collaboration Website" <info@fynboscorridors.org>'
            recipient = f"{manager.name} <{manager.email}>"

            send_mail(
                "Manage garden information: " + info.name,
                msg_plain,
                sender,
                [recipient],
                html_message=msg_html,
            )
            messages.success(request, f"We have send you an e-mail link to modify the garden information. Please check your Notifications or Spam folder if you don't see this.")
        else:
            messages.error(request, f"Your e-mail address was not found. Are you sure this was registered? If so, please <a href='contact'>contact us</a> and we will correct this.")

    context = {
        "no_index": True,
        "info": info,
    }
    return render(request, "core/garden.manager.html", context)


def vegetation_types(request):
    context = {
        "all": VegetationType.objects.all(),
        "page": Page.objects.get(pk=1),
    }
    return render(request, "core/vegetationtypes.html", context)

def vegetation_type(request, slug):

    info = get_object_or_404(VegetationType, slug=slug)

    if "download" in request.POST:
        geo = info.spaces.all()[0].geometry
        response = HttpResponse(geo.geojson, content_type="application/json")
        response["Content-Disposition"] = f"attachment; filename=\"{info.name}.geojson\""
        return response

    map = folium.Map(
        zoom_start=14,
        scrollWheelZoom=False,
        tiles=STREET_TILES,
        attr="Mapbox",
    )

    Fullscreen().add_to(map)

    for each in info.spaces.all():
        folium.GeoJson(
            each.geometry.geojson,
            name="geojson",
        ).add_to(map)

    map.fit_bounds(map.get_bounds())

    context = {
        "info": info,
        "map": map._repr_html_(),
    }
    return render(request, "core/vegetationtype.html", context)

def profile(request, section=None, lat=None, lng=None, id=None, subsection=None):

    vegetation = get_object_or_404(Document, pk=983172)
    veg = None
    link = None

    if "next" in request.POST:
        return redirect("rehabilitation_design")

    if not lat:
        lat = request.COOKIES.get("lat")
        lng = request.COOKIES.get("lng")

    if lat and lng:
        link = f"/profile/{lat},{lng}/"

    try:
        lat = float(lat)
        lng = float(lng)
        center = geos.Point(lng, lat)
        veg = vegetation.spaces.get(geometry__intersects=center)
        veg = VegetationType.objects.get(spaces=veg)
        suburb = ReferenceSpace.objects.filter(source_id=334434, geometry__intersects=center)
        species = Species.objects.filter(vegetation_types=veg)
        if suburb:
            suburb = suburb[0].name.title()
    except:
        messages.warning(request, f"We are unable to locate the relevant vegetation type. Please make sure to <a href='/fynbos-rehabilitation/site-selection/'>select a site on the map</a> first, so that we can load the relevant plant species for your chosen location.")
        suburb = None
        species = None

    context = {
        "lat": lat,
        "lng": lng,
        "link": link,
        "info": veg,
        "section": section,
        "subsection": subsection,
        "suburb": suburb,
        "page": Page.objects.get(slug="plant-selection"),
        "species": species,
    }

    if section == "plants":

        if subsection == "pioneers":
            context["title"] = "Pioneer species"
            species = species.filter(features__id=125)
            context["species_list"] = species

        elif subsection == "birds":
            context["title"] = "Bird-friendly species"
            context["sugarbird_list"] = species.filter(features__id__in=[111,113,114])
            context["sunbird_list"] = species.filter(features__id=133)
            context["bird_list"] = species.filter(features__id=109)

        elif subsection == "insects":
            context["title"] = "Insect-friendly species"
            context["bee_list"] = species.filter(features__id=110)
            context["monkeybeetle_list"] = species.filter(features__id=112)

        elif subsection == "edible":
            context["title"] = "Edible plant species"
            species = species.filter(features__id=123)
            context["species_list"] = species

        elif subsection == "medicinal":
            context["title"] = "Medicinal plant species"
            species = species.filter(features__id=115)
            context["species_list"] = species

        context["photos_first"] = True

    elif section == "nearby":
        
        files = {
            "schools": 983409,
            "cemeteries": 983426,
            "parks": 983479,
            "rivers": 983382,
            "remnants": 983097,
        }

        capetown = get_object_or_404(ReferenceSpace, pk=988911)
        source_document = get_object_or_404(Document, pk=files[subsection])

        center = geos.Point(x=lng, y=lat, srid=4326)
        center.transform(3857) # Transform Projection to Web Mercator     
        radius = 1000 # Number of meters distance
        circle = center.buffer(radius) 
        circle.transform(4326) # Transform back to WGS84 to create geojson

        layer = source_document.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))

        if not layer:
            radius = 2000 # Number of meters distance
            circle = center.buffer(radius) 
            circle.transform(4326) # Transform back to WGS84 to create geojson

            messages.warning(request, "We could not find anything in the regular area search, so we expanded our search to cover a wider area.")
            layer = source_document.spaces.filter(Q(geometry__within=circle)|Q(geometry__intersects=circle))

        map = folium.Map(
            location=[lat,lng],
            zoom_start=14,
            scrollWheelZoom=False,
            tiles=STREET_TILES,
            attr="Mapbox",
        )

        folium.GeoJson(
            circle.geojson,
            name="geojson",
        ).add_to(map)

        Fullscreen().add_to(map)

        satmap = folium.Map(
            location=[lat,lng],
            zoom_start=17,
            scrollWheelZoom=False,
            tiles=SATELLITE_TILES,
            attr="Mapbox",
        )

        def style_function(feature):
            return {
                "fillOpacity": 0,
                "weight": 4,
                "color": "#fff",
            }

        folium.GeoJson(
            circle.geojson,
            name="geojson",
            style_function=style_function,
        ).add_to(satmap)

        satmap.fit_bounds(map.get_bounds())
        Fullscreen().add_to(satmap)

        folium.GeoJson(
            capetown.geometry.geojson,
            name="geojson",
            style_function=style_function,
        ).add_to(satmap)

        for each in layer:
            geom = each.geometry.intersection(circle)

            folium.GeoJson(
                geom.geojson,
                name="geojson",
            ).add_to(map)

            folium.GeoJson(
                geom.geojson,
                name="geojson",
            ).add_to(satmap)

        context["map"] = map._repr_html_()
        context["satmap"] = satmap._repr_html_()
        context["layer"] = layer
        context["source"] = source_document

    return render(request, "core/profile.html", context)

def photos(request, garden=None, photo=None):
    photos = Photo.objects.filter(garden__isnull=False)
    if garden:
        photos = photos.filter(garden_id=garden)
        garden = Garden.objects.get(pk=garden)
    paginator = Paginator(photos, 60)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if photo:
        photo = photos.get(pk=photo)

    context = {
        "photos": page_obj,
        "photo": photo,
        "garden": garden,
    }
    return render(request, "core/photos.html", context)

def corridors_rivers_methodology(request):

    rivers = ReferenceSpace.objects.filter(source_id=983382, meta_data__poor_quality_river=True)
    river_segments = Document.objects.get(pk=5)
    river_buffer = Document.objects.get(pk=3)
    bionet_flat = Document.objects.get(pk=4)
    bionet_buffer = Document.objects.get(pk=6)

    context = {
        "rivers": rivers,
        "river_segments": river_segments.spaces.all()[0].geometry,
        "river_buffer": river_buffer.spaces.all()[0].geometry,
        "bionet_flat": bionet_flat.spaces.all()[0].geometry,
        "bionet_buffer": bionet_buffer.spaces.all()[0].geometry,
        "load_map": True,
        "lat": -33.9790,
        "lng": 18.5284,
        "corridors": Corridor.objects.all(),
        "page": "methodology",
        # Run this if the rivers should show, e.g. for screenshotting
        #"final_rivers": [989882, 990004, 990036, 989903, 990127, 989920, 989924, 990032, 990020],
    }
    return render(request, "core/corridors.rivers.methodology.html", context)

def update_map(request):

    rivers = ReferenceSpace.objects.filter(source_id=983382, meta_data__poor_quality_river=True)

    # ONCE OFF DOCUMENT CREATION

    river_segments = Document.objects.filter(name="Rivers with poor quality and not close to Bionet")
    if river_segments:
        river_segments = river_segments[0]
    else:
        river_segments = Document.objects.create(
            name = "Rivers with poor quality and not close to Bionet",
            content = "This document contains the rivers (with buffer) that are NOT close to bionet. It is used for our priority map. It can be auto-generated through code that is run in the priority_map() function in views.py. Do not edit this map manually.",
        )

    river_buffer = Document.objects.filter(name="Poor quality rivers with buffer")
    if river_buffer:
        river_buffer = river_buffer[0]
    else:
        river_buffer = Document.objects.create(
            name = "Poor quality rivers with buffer",
            content = "This document is generated by taking low-quality rivers and giving them a certain buffer. It is used for our priority map. It can be auto-generated through code that is run in the priority_map() function in views.py. Do not edit this map manually.",
        )

    bionet_flat = Document.objects.filter(name="Bionet - flat file")
    if bionet_flat:
        bionet_flat = bionet_flat[0]
    else:
        bionet_flat = Document.objects.create(
            name = "Bionet - flat file",
            content = "This document contains all of bionet, but all elements are grouped together. It is used for our priority map. It can be auto-generated through code that is run in the priority_map() function in views.py. Do not edit this map manually.",
        )

    bionet_buffer = Document.objects.filter(name="Bionet - with buffer")
    if bionet_buffer:
        bionet_buffer = bionet_buffer[0]
    else:
        bionet_buffer = Document.objects.create(
            name = "Bionet - with buffer",
            content = "This document contains all of bionet, but all elements are grouped together and given a buffer. It is used for our priority map. It can be auto-generated through code that is run in the priority_map() function in views.py. Do not edit this map manually.",
        )

    # MARK ALL THE RIVERS
    if "new_rivers" in request.GET:
        rivers = get_object_or_404(Document, pk=983382)
        badrivers = [
            "DIEP RIVER",
            "DIEPRIVIER",
            "EERSTE RIVER",
            "EERSTERIVIER",
            "ELSIESKRAAL",
            "ELSIESKRAAL CANAL",
            "extension of channel into Salt",
            "extension of Liesbeek into Salt",
            "KUILS RIVER",
            "KUILSRIVIER CHANNEL",
            "MOSSELBANK RIVER",
            "MOSSELBANKRIVIER",
            "SALT RIVER",
            "SAND RIVER",
            "SANDRIVIER",
            "SIR LOWRY'S PASS RIVER",
            "stream extension to Eerste River",
            "ZEEKOEVLEI",
            "ZEEKOEVLEI CANAL",
            "BIG LOTUS RIVER CANAL", # Manually added
            "BIG LOTUS RIVER/NYANGA CANAL", # Manually added
        ]
        a = []
        for each in rivers.spaces.all():
            if each.name in badrivers:
                each.meta_data = {"poor_quality_river": True}
                each.save()
        messages.success(request, f"New rivers are indexed! poor_quality_river=True in meta_data")

    if "update" in request.GET:
        from django.contrib.gis.db.models import Union
        from django.contrib.gis.db.models.functions import MakeValid

        combined = rivers.aggregate(union=Union("geometry"))
        geo = combined["union"]

        # Adding a buffer as per: https://gis.stackexchange.com/questions/228988/add-buffer-around-polygon-in-meters-using-geodjango
        distance = 400 # distance in meter
        buffer_width = distance / 40000000.0 * 360.0
        geo = geo.buffer(buffer_width)

        ReferenceSpace.objects.create(
            name = "Rivers with buffer",
            content = f"Automatically created from the original shapefile, by adding a {distance}m buffer.",
            source = river_buffer,
            geometry = geo,
        )
        messages.success(request, f"We created RIVERS WITH BUFFERS with {distance}m distance")

        bionet = Document.objects.get(pk=983134)

        spaces = bionet_flat.spaces.all()
        spaces.delete()

        # We had invalid geometry in the Bionet shapefile. It is now fixed, but if we 
        # have new geometry that is again invalid, then run this again:
        #bionet.spaces.all().update(geometry=MakeValid("geometry"))

        combined = bionet.spaces.all().aggregate(union=Union("geometry"))
        geo = combined["union"]

        ReferenceSpace.objects.create(
            name = "Bionet in a single layer",
            content = f"Automatically created from the original shapefile, unified into a single layer.",
            source = bionet_flat,
            geometry = geo,
        )
        messages.success(request, f"We created bionet as a single layer")

        space = bionet_flat.spaces.all()[0]
        geo = space.geometry
        distance = 400 # distance in meter
        buffer_width = distance / 40000000.0 * 360.0
        geo = geo.buffer(buffer_width)

        ReferenceSpace.objects.create(
            name = "Bionet with a buffer",
            content = f"Automatically created from the original shapefile, with a buffer of {buffer_width}m.",
            source = bionet_buffer,
            geometry = geo,
        )
        messages.success(request, f"We created BIONET WITH BUFFERS with {distance}m distance")

    #### END OF UPDATING CODE ####

    if "calculate_difference" in request.GET:
        geo_bionet = bionet_buffer.spaces.all()[0].geometry        
        geo_rivers = river_buffer.spaces.all()[0].geometry        

        spaces = river_segments.spaces.all()
        spaces.delete()

        geo = geo_rivers.difference(geo_bionet)
        ReferenceSpace.objects.create(
            name = "Rivers far from Bionet",
            content = f"Automatically created from the original shapefile.",
            source = river_segments,
            geometry = geo,
        )

    ### END OF SECOND UPDATING PART OF CODE

    return render(request, "core/map.update.html")

def page(request, slug):

    if slug == "fynbos-rehabilitation":
        check = Page.objects.filter(slug=slug)
        if not check:
            Page.objects.create(name="Fynbos rehabilitation", position=0, format="MARK")

    info = get_object_or_404(Page, slug=slug)
    context = {
        "page": info,
    }
    return render(request, "core/page.html", context)

def corridors_rivers(request):
    context = {
        "info": Page.objects.get(slug="high-impact-strategic-river-corridors"),
        "corridors": Corridor.objects.all(),
    }
    return render(request, "core/corridors.rivers.html", context)

def corridor_rivers(request, id):
    context = {
        "info": get_object_or_404(Corridor, pk=id),
        "corridors": Corridor.objects.all(),
    }
    return render(request, "core/corridor.rivers.html", context)

def corridors_overview(request):
    context = {}
    return render(request, "core/corridors.overview.html", context)

def corridors(request):
    context = {
        "info": Page.objects.get(slug="fynbos-corridors"),
    }
    return render(request, "core/corridors.introduction.html", context)

def user_login(request):
    redirect_url = "index"
    if request.GET.get("next"):
        redirect_url = request.GET.get("next")

    if request.user.is_authenticated:
        return redirect(redirect_url)

    if request.method == "POST":
        email = request.POST.get("email").lower()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You are logged in.")
            return redirect(redirect_url)
        else:
            messages.error(request, "We could not authenticate you, please try again.")

    context = {
    }
    return render(request, "core/login.html", context)

def user_logout(request):
    logout(request)
    messages.warning(request, "You are now logged out")

    if "next" in request.GET:
        return redirect(request.GET.get("next"))
    else:
        return redirect("index")

def newsletter(request):
    if request.POST and "email" in request.POST:
        Newsletter.objects.create(email=request.POST.get("email"))
        messages.success(request, "Thank you! You have been registered for our newsletter.")
    else:
        messages.warning(request, "We could not register you for our newsletter - please ensure you enter a valid email address. Try again in the footer below.")

    if "next" in request.POST:
        return redirect(request.POST.get("next"))
    else:
        return redirect("index")

def organizations(request):
    context = {
        "organizations": Organization.objects.filter(part_of_fcc=True),
    }
    return render(request, "core/organizations.html", context)

def documents(request):
    context = {
        "documents": Document.objects.filter(active=True, type__in=[6,7]).order_by("name"),
    }
    return render(request, "core/documents.html", context)

