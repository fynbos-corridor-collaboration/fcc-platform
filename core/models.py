from django.db import models
from django.contrib.gis.db import models
from stdimage.models import StdImageField
from django.utils.text import slugify
from markdown import markdown
from django.utils.safestring import mark_safe
from django.conf import settings
import bleach
from unidecode import unidecode
from django.urls import reverse

class Page(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    content_html = models.TextField(null=True, blank=True, help_text="Auto-generated - do NOT edit")
    image = StdImageField(upload_to="pages", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)}, null=True, blank=True)
    position = models.PositiveSmallIntegerField(db_index=True)
    slug = models.SlugField(max_length=255)
    FORMATS = (
        ("HTML", "HTML"),
        ("MARK", "Markdown"),
        ("MARK_HTML", "Markdown and HTML"),
    )
    format = models.CharField(max_length=9, choices=FORMATS)

    def __str__(self):
        return self.name

    def get_content(self):
        # The content field is already sanitized, according to the settings (see the save() function below)
        # So when we retrieve the html content we can trust this is safe, and will mark it as such
        # We avoid using |safe in templates -- to centralize the effort to sanitize input
        if self.content:
            return mark_safe(self.content_html)
        else:
            return ""

    class Meta:
        ordering = ["position"]

    def save(self, *args, **kwargs):
        if not self.content:
            self.content_html = None
        elif self.format == "HTML":
            # Here it wouldn't hurt to apply bleach and take out unnecessary tags
            self.content_html = self.content
        elif self.format == "MARK_HTML":
            # Here it wouldn't hurt to apply bleach and take out unnecessary tags
            self.content_html = markdown(self.content)
        elif self.format == "MARK":
            self.content_html = markdown(bleach.clean(self.content))
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

class Organization(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    logo = StdImageField(upload_to="pages", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)}, delete_orphans=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    part_of_fcc = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Document(models.Model):
    name = models.CharField(max_length=255, db_index=True)

    class Type(models.IntegerChoices):
        UNKNOWN = 0, "Unknown"
        NATURE = 1, "Nature"
        CONNECTOR = 2, "Connector layers"
        TRANSPORT = 3, "Transport"
        POTENTIAL = 4, "Potential sites"
        CONTEXT = 5, "Context"

    type = models.IntegerField(choices=Type.choices, db_index=True, default=0)
    author = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    content = models.TextField("Description", null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True, help_text="See https://htmlcolors.com/color-names for an overview of possible color names")
    meta_data = models.JSONField(null=True, blank=True, help_text="Only to be edited if you know what this does - otherwise, please do not change")
    active = models.BooleanField(default=True, db_index=True)
    include_in_site_analysis = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.name

    @property
    def get_dataviz(self):
        if self.meta_data and "dataviz" in self.meta_data:
            return self.meta_data["dataviz"]
        else:
            return {}

    @property
    def get_absolute_url(self):
        return "/maps/" + str(self.id)

    # Returns the opacity used for the background color in maps
    # Some layers, such as the boundary layer, should be fully 
    # transparent so we only see a border.
    @property
    def get_opacity(self):
        try:
            return self.meta_data["opacity"]
        except:
            return 0.4 # Default background color opacity in the maps

class ReferenceSpace(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="referencespace")
    source = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, related_name="spaces")
    temp_source_id = models.IntegerField(null=True, blank=True, help_text="Only used when importing data")
    meta_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.source.name})"

    @property
    def get_absolute_url(self):
        if hasattr(self, "garden"):
            return f"/gardens/{self.id}/"
        else:
            return f"/space/{self.id}/"

    @property
    def get_lat(self):
        try:
            return self.geometry.centroid[1]
        except:
            return None

    @property
    def get_lng(self):
        try:
            return self.geometry.centroid[0]
        except:
            return None

    def get_vegetation_type(self):
        v = VegetationType.objects.filter(spaces=self)
        return v[0] if v else None

    @property
    def get_photo_medium(self):
        if self.photo:
            return self.photo.image.medium.url
        else:
            return settings.MEDIA_URL + "/placeholder.png"

    def __str__(self):
        return self.name if self.name else "Unnamed garden"

    @property
    def suburb(self):
        if not self.geometry:
            return None
        suburb = ReferenceSpace.objects.filter(source_id=334434, geometry__intersects=self.geometry)
        if suburb:
            return suburb[0].name.title()
        else:
            return None
    
    def get_popup(self):
        content = f"<h4>{self.name}</h4>"
        if self.photo:
            content = content + f"<a class='d-block' href='{self.get_absolute_url}'><img alt='{self.name}' src='{self.photo.image.thumbnail.url}' /></a><hr>"
        content = content + f"<a href='{self.get_absolute_url}'>View details</a>"
        return mark_safe(content)

    class Meta:
        ordering = ["name"]

class Garden(ReferenceSpace):
    active = models.BooleanField(default=True, db_index=True)
    original = models.JSONField(null=True, blank=True)

    class PhaseStatus(models.IntegerChoices):
        PENDING = 1, "Pending"
        IN_PROGRESS = 2, "In progress"
        COMPLETED = 3, "Completed"

    phase_assessment = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    phase_alienremoval = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    phase_landscaping = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    phase_pioneers = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    phase_birdsinsects = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    phase_specialists = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    phase_placemaking = models.IntegerField(choices=PhaseStatus.choices, db_index=True, null=True)
    organizations = models.ManyToManyField(Organization, blank=True)
    vegetation_type = models.ForeignKey("VegetationType", on_delete=models.CASCADE, null=True, blank=True, related_name="gardens")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        vegetation = Document.objects.get(pk=983172)
        veg = None
        if self.geometry:
            try:
                veg = vegetation.spaces.get(geometry__intersects=self.geometry.centroid)
                veg = veg.get_vegetation_type()
            except:
                veg = None
            self.vegetation_type = veg
        super().save(*args, **kwargs)

class Event(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Genus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Genera"

    def get_absolute_url(self):
        return reverse("genus", args=[self.id])

class Family(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse("family", args=[self.id])

class Redlist(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=2)
    css = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def get_code(self):
        return mark_safe(f"<span class='badge bg-{self.css}'>{self.code}</span>")

    @property
    def formatted(self):
        return mark_safe(f"{self.get_code} {self.name}")

    class Meta:
        verbose_name_plural = "Redlist"

class VegetationType(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    historical_cover = models.PositiveSmallIntegerField(help_text="Cover in km2")
    cape_town_cover = models.FloatField(help_text="In %")
    current_cape_town_area = models.FloatField(help_text="In km2")
    conserved_cape_town = models.PositiveSmallIntegerField(help_text="Conserved or managed, in km2")
    redlist = models.ForeignKey(Redlist, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255)
    spaces = models.ManyToManyField(ReferenceSpace, blank=True, limit_choices_to={"source_id": 983172})

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("vegetation_type", args=[self.slug])

    class Meta:
        ordering = ["name"]

class SpeciesFeatures(models.Model):
    name = models.CharField(max_length=255, db_index=True)

    class Type(models.IntegerChoices):
        ANIMALS = 1, "Animal-friendly"
        SITE = 2, "Tolerances/sites"
        GROWTH = 3, "Growth features"
        OTHER = 4, "Other"

    type = models.IntegerField(choices=Type.choices, db_index=True, default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Species(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    common_name = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    common_name_xh = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    common_name_af = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    redlist = models.ForeignKey(Redlist, on_delete=models.CASCADE, null=True, blank=True)
    links = models.JSONField(null=True, blank=True)
    animals = models.JSONField(null=True, blank=True)
    soils = models.JSONField(null=True, blank=True)
    properties = models.JSONField(null=True, blank=True)
    propagation_seed = models.TextField(null=True, blank=True)
    propagation_cutting = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    genus = models.ForeignKey(Genus, on_delete=models.CASCADE, related_name="species")
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True, related_name="species")
    features = models.ManyToManyField(SpeciesFeatures, blank=True, related_name="species")
    vegetation_types = models.ManyToManyField(VegetationType, blank=True, related_name="species")
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="main_species")
    meta_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Species"

    @property
    def get_photo_medium(self):
        if self.photo:
            return self.photo.image.medium.url
        else:
            return settings.MEDIA_URL + "/placeholder.png"

    @property
    def get_photo_thumbnail(self):
        if self.photo:
            return self.photo.image.thumbnail.url
        else:
            return settings.MEDIA_URL + "/placeholder.png"

    def old(self):
        return self.meta_data.get("original")

    def get_links(self):
        links = {}
        original = self.meta_data.get("original")
        if original.get("link"):
            link = original.get("link")
            if "wikipedia" in link:
                links["Wikipedia"] = link
            elif "pza" in link:
                links["PlantZA"] = link
            elif "redlist" in link:
                links["Redlist"] = link
            else:
                links[link] = link

        if original.get("link_plantza"):
            links["PlantZA"] = original.get("link_plantza")

        if original.get("link_wikipedia"):
            links["Wikipedia"] = original.get("link_wikipedia")

        if original.get("link_extra"):
            links["More information"] = original.get("link_extra")

        if original.get("link_redlist"):
            links["Redlist"] = original.get("link_redlist")

        return links

class Photo(models.Model):
    name = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = StdImageField(upload_to="photos", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)}, delete_orphans=True)
    position = models.PositiveSmallIntegerField(db_index=True, default=1)
    date = models.DateField(auto_now_add=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")
    species = models.ForeignKey(Species, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")

    old_id = models.IntegerField(db_index=True, null=True, blank=True) # Delete after migration is complete
    original = models.JSONField(null=True, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Photo {self.id}"

    @property
    def get_photo_medium(self):
        return self.image.medium.url

    @property
    def get_photo_thumbnail(self):
        return self.image.thumbnail.url

    class Meta:
        ordering = ["position", "date"]

class Corridor(models.Model):
    name = models.CharField(max_length=255)
    general_description = models.TextField(null=True, blank=True)
    social_description = models.TextField(null=True, blank=True)
    image = StdImageField(upload_to="corridors", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)}, delete_orphans=True)
    wards = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

    @property
    def get_absolute_url(self):
        return f"/corridors/rivers/{self.id}/"

    def get_image_size(self):
        return self.image.size/1024

class Newsletter(models.Model):
    email = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ["email"]
