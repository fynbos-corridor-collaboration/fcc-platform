from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import urllib.request, json 
from django.contrib import messages
from django.utils.safestring import mark_safe
import folium
from folium.plugins import Fullscreen
import random
from django.db.models import Count

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
    if "import_species" in request.GET:
        import csv

        Species.objects.all().delete()
        Genus.objects.all().delete()
        Family.objects.all().delete()
        with open(settings.MEDIA_ROOT + "/import/species.csv", "r", encoding="utf-8-sig") as csvfile:
            contents = csv.DictReader(csvfile)
            items = []
            for row in contents:
                if not row["genus"]:
                    a = row["name"]
                    a = a.split(" ")
                    row["genus"] = a[0]
                genus = Genus.objects.filter(name=row["genus"])
                if not genus:
                    genus = Genus.objects.create(name=row["genus"])
                else:
                    genus = genus[0]
                family = None
                if row["family"]:
                    f = row["family"].capitalize()
                    f = f.strip()
                    family = Family.objects.filter(name=f)
                    if not family:
                        family = Family.objects.create(name=f)
                    else:
                        family = family[0]
                links = []
                if row["link"]:
                    links.append(row["link"])
                if row["link_plantza"]:
                    links.append(row["link_plantza"])
                if row["link_wikipedia"]:
                    links.append(row["link_wikipedia"])
                if row["link_redlist"]:
                    links.append(row["link_redlist"])
                if row["link_extra"]:
                    links.append(row["link_extra"])
                items.append(Species(
                    name = row["scientific_name"],
                    common_name = row["name"],
                    common_name_xh = row["name_isixhosa"],
                    common_name_af = row["name_afrikaans"],
                    description = row["description"],
                    genus = genus,
                    family = family,
                    links = links,
                    meta_data = { "original": row},
                ))
            Species.objects.bulk_create(items)

    if "features" in request.GET:
        species = Species.objects.all()
        for each in species:
            pass

    if "species_images" in request.GET:
        from django.core.files.uploadedfile import UploadedFile
        species = Species.objects.all()
        for each in species:
            try:
                credit = each.meta_data["original"]["image_credit"]
                if each.meta_data["original"]["image_link"]:
                    credit += " (" + each.meta_data["original"]["image_link"] + ")"
                id = each.meta_data["original"]["id"]
                path = settings.MEDIA_ROOT + f"/species/{id}.jpg"
                photo = Photo.objects.create(
                    image = UploadedFile(file=open(path, "rb")),
                    author = credit,
                    species = each,
                )
                each.photo = photo
                each.save()

            except Exception as e:
                print(id)
                print(each)
                print(each.id)
                print(e)
    if "clean_species" in request.GET:
        names = ["Spinach", "Beetroot", "Onion", "Cauliflower"]
        a = Species.objects.filter(common_name__in=names)
        a.delete()

    if "species_fix" in request.GET:
        all = Species.objects.all()

        features = {
            'bird_friendly': 'This is a bird-friendly species',
            'honeybees': 'This will attract honey bees',
            'cape_sugarbird': 'Will attract the Cape Sugarbird',
            'monkey_beetle': 'Will attract monkey beetles',
            'malachite_sunbird': 'Will attract the Malachite Sugarbird',
            'orange_breasted_sunbird': 'Will attract the Orange-breasted Sugarbird',
            'medicinal': 'It provides medicinal value',
            'first_year': 'It is a pioneer species suitable for establishing the soil in bare areas',
            'construction': 'It can be used as a construction material',
            'sensitive_roots': 'Sensitive roots',
            'wind_resistant': 'Wind resistant',
            'fast_growing': 'Fast-growing',
            'drought_resistant': 'Drought-resistant',
            'fragrant': 'Fragrant',
            'edible': 'Edible',
            'good_potplant': 'Good potplant',
            'pioneer': 'Pioneer species',
            'easy_to_grow': 'Easy to grow',
            'coastal_areas': 'Good for coastal areas',
            'hedge': 'Can be used as a hedge',
            'butterflies': 'Attracts butterflies',
            'wet_sites': 'Suitable for wet sites',
            'clay_soil': 'Suitable for clay soil',
            'sandy_soil': 'Suitable for sandy soil',
        }

        match = {}
        a = SpeciesFeatures.objects.all()
        a.delete()
        for key,value in features.items():
            match[key] = SpeciesFeatures.objects.create(name=value)
        for each in all:
            for key,value in features.items():
                if key in each.meta_data["original"] and each.meta_data["original"][key]:
                    t = int(each.meta_data["original"][key])
                    if t == 1:
                        each.features.add(match[key])
                        p(f"Yes, we found {key} in {each}")
                        p(each.meta_data["original"][key])
            each.save()


    if "import_veg" in request.GET:
        import csv

        VegetationType.objects.all().delete()
        redlist = Redlist.objects.all()
        if not redlist:
            r = {
                "EX": "Extinct",
                "EW": "Extinct in the Wild",
                "CR": "Critically Endangered",
                "EN": "Endangered",
                "VU": "Vulnerable",
                "NT": "Near threatened",
                "CD": "Conservation Dependent",
                "LC": "Least Concern",
                "DD": "Data Deficient",
                "NE": "Not Evaluated",
            }
            for key,value in r.items():
                Redlist.objects.create(code=key, name=value)

        with open(settings.MEDIA_ROOT + "/import/vegetation_types.csv", "r", encoding="utf-8-sig") as csvfile:
            contents = csv.DictReader(csvfile)
            items = []
            for row in contents:
                redlist = row["conservation_status"]

                VegetationType.objects.create(
                    id = row["id"],
                    name = row["name"],
                    description = row["description"],
                    historical_cover = row["historical_cover"],
                    cape_town_cover = row["percentage_capetown"],
                    current_cape_town_area = row["current_cover"],
                    conserved_cape_town = row["conservation_area"],
                    redlist = Redlist.objects.get(code=row["conservation_status"]),
                    slug = row["slug"],
                )

    context = {}
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
    }
    return render(request, "core/space.html", context)


def maps(request):
    types = Document.Type
    parents = []
    hits = {}
    type_list = {}
    getcolors = {}
    for each in types:
        e = int(each)
        parents.append(e)
        hits[e] = []
        type_list[e] = each.label

    documents = Document.objects.filter(active=True).order_by("type")
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
        "icons": {
            1: "leaf",
            2: "draw-square",
            3: "train",
            4: "map-marker",
            5: "info-circle",
        }
    }
    return render(request, "core/maps.html", context)

def report(request):
    info = get_object_or_404(ReferenceSpace, pk=988911)
    schools = get_object_or_404(Document, pk=983409)
    cemeteries = get_object_or_404(Document, pk=983426)
    parks = get_object_or_404(Document, pk=983479)
    rivers = get_object_or_404(Document, pk=983382)
    remnants = get_object_or_404(Document, pk=983097)
    vegetation = get_object_or_404(Document, pk=983356)

    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
    except:
        lat = -33.9641
        lng = 18.5113

    from django.contrib.gis import geos
    center = geos.Point(lng, lat)

    radius = 0.01
    circle = center.buffer(radius)

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

    if info.geometry.geom_type != "Point":
        # For a point we want to give some space around it, but polygons should be
        # an exact fit
        map.fit_bounds(map.get_bounds())

    Fullscreen().add_to(map)

    satmap = folium.Map(
        location=[lat,lng],
        zoom_start=17,
        scrollWheelZoom=False,
        tiles=SATELLITE_TILES,
        attr="Mapbox",
    )

    folium.GeoJson(
        circle.geojson,
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

    parkmap = folium.Map(
        location=[lat,lng],
        zoom_start=15,
        scrollWheelZoom=False,
        tiles=LIGHT_TILES,
        attr="Mapbox",
    )
    folium.GeoJson(
        circle.geojson,
        name="geojson",
    ).add_to(parkmap)
    parks = parks.spaces.filter(geometry__within=circle)
    for each in parks:
        folium.GeoJson(
            each.geometry.geojson,
            name="geojson",
        ).add_to(parkmap)

    cemeteriesmap = folium.Map(
        location=[lat,lng],
        zoom_start=15,
        scrollWheelZoom=False,
        tiles=LIGHT_TILES,
        attr="Mapbox",
    )
    folium.GeoJson(
        circle.geojson,
        name="geojson",
    ).add_to(cemeteriesmap)
    cemeteries = cemeteries.spaces.filter(geometry__within=circle)
    for each in cemeteries:
        folium.GeoJson(
            each.geometry.geojson,
            name="geojson",
        ).add_to(cemeteriesmap)

    schoolmap = folium.Map(
        location=[lat,lng],
        zoom_start=15,
        scrollWheelZoom=False,
        tiles=LIGHT_TILES,
        attr="Mapbox",
    )
    folium.GeoJson(
        circle.geojson,
        name="geojson",
    ).add_to(schoolmap)
    schools = schools.spaces.filter(geometry__within=circle)
    for each in schools:
        folium.GeoJson(
            each.geometry.geojson,
            name="geojson",
        ).add_to(schoolmap)

    remnantmap = folium.Map(
        location=[lat,lng],
        zoom_start=15,
        scrollWheelZoom=False,
        tiles=LIGHT_TILES,
        attr="Mapbox",
    )
    folium.GeoJson(
        center.geojson,
        name="geojson",
    ).add_to(remnantmap)
    #remnants = remnants.spaces.filter(geometry__within=circle)
    from django.contrib.gis.measure import D
    remnants = remnants.spaces.filter(geometry__distance_lte=(center, D(km=3)))
    for each in remnants:
        folium.GeoJson(
            each.geometry.geojson,
            name="geojson",
        ).add_to(remnantmap)

    rivermap = folium.Map(
        location=[lat,lng],
        zoom_start=15,
        scrollWheelZoom=False,
        tiles=LIGHT_TILES,
        attr="Mapbox",
    )
    folium.GeoJson(
        circle.geojson,
        name="geojson",
    ).add_to(rivermap)
    rivers = rivers.spaces.filter(geometry__crosses=circle)
    for each in rivers:
        geom = each.geometry.intersection(circle)
        folium.GeoJson(
            geom.geojson,
            name="geojson",
        ).add_to(rivermap)

    try:
        veg = vegetation.spaces.filter(geometry__intersects=center)
        veg = veg[0]
    except:
        veg = None

    context = {
        "map": map._repr_html_(),
        "satmap": satmap._repr_html_(),
        "parkmap": parkmap._repr_html_(),
        "parks": parks,
        "cemeteriesmap": cemeteriesmap._repr_html_(),
        "cemeteries": cemeteries,
        "rivermap": rivermap._repr_html_(),
        "rivers": rivers,
        "remnantmap": remnantmap._repr_html_(),
        "remnants": remnants,
        "schoolmap": schoolmap._repr_html_(),
        "schools": schools,
        "veg": veg,
        "center": center,
    }
    return render(request, "core/report.html", context)

def geojson(request, id):
    info = Document.objects.get(pk=id)
    features = []
    spaces = info.spaces.all()
    if "space" in request.GET:
        spaces = spaces.filter(id=request.GET["space"])
    geom_type = None
    for each in spaces:
        if each.geometry:
            url = each.get_absolute_url
            content = ""
            content = content + f"<a href='{url}'>View details</a>"
            content = content + f"<br><a href='/maps/{info.id}'>View {info}</a>"
            if not geom_type:
                geom_type = each.geometry.geom_type
            features.append({
                "type": "Feature",
                "geometry": json.loads(each.geometry.json),
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

def species_overview(request):
    samples = [15,21,51,81,83,218,230,270,301,313]
    context = {
        "genus": Genus.objects.all(),
        "family": Family.objects.all(),
        "load_datatables": True,
        "samples": Photo.objects.filter(pk__in=random.sample(samples, 4)),
        "all": Species.objects.all().count(),
        "features": SpeciesFeatures.objects.all(),
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
    full_list = full_list.annotate(total=Count("species"))
    context = {
        "load_datatables": True,
        "genus": genus,
        "family": family,
        "species_list": species,
        "full_list": full_list,
    }
    return render(request, "core/species.list.html", context)

def species_full_list(request):
    species = Species.objects.all()
    features = None
    if "feature" in request.GET:
        features = SpeciesFeatures.objects.filter(pk__in=request.GET.getlist("feature"))
        for each in features:
            species = species.filter(features=each)
    context = {
        "species_list": species,
        "load_datatables": True,
        "features": features,
    }
    return render(request, "core/species.all.html", context)

def species(request, id):
    context = {
        "info": get_object_or_404(Species, pk=id),
    }
    return render(request, "core/species.html", context)

def vegetation_types(request):
    context = {
        "all": VegetationType.objects.all(),
        "page": Page.objects.get(pk=1),
    }
    return render(request, "core/vegetationtypes.html", context)

def vegetation_type(request, slug):
    context = {
        "info": get_object_or_404(VegetationType, slug=slug),
    }
    return render(request, "core/vegetationtype.html", context)

