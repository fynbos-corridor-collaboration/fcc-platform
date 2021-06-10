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

class Garden(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="gardens")

    def __str__(self):
        return self.name

class Document(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    meta_data = models.JSONField(null=True, blank=True)
    active = models.BooleanField(default=True, db_index=True)

    class Type(models.IntegerChoices):
        UNKNOWN = 0, "Unknown"
        NATURE = 1, "Nature"
        CONNECTOR = 2, "Connector layers"
        TRANSPORT = 3, "Transport"
        POTENTIAL = 4, "Potential sites"
        CONTEXT = 5, "Context"

    type = models.IntegerField(choices=Type.choices, db_index=True, default=0)

    def __str__(self):
        return self.name

    @property
    def get_dataviz(self):
        if self.meta_data and "dataviz" in self.meta_data:
            return self.meta_data["dataviz"]
        else:
            return {}

    content = models.TextField(null=True, blank=True)

class ReferenceSpace(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="referencespace")
    source = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, related_name="spaces")
    temp_source_id = models.IntegerField(null=True, blank=True, help_text="Only used when importing data")

    def __str__(self):
        return f"{self.name} ({self.source.name})"

    @property
    def get_absolute_url(self):
        return "/space/" + str(self.id)

    class Meta:
        ordering = ["name"]

class Corridor(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Organization(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    logo = StdImageField(upload_to="pages", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Genus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse("genus", args=[self.id])

class Family(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

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

class VegetationType(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    historical_cover = models.PositiveSmallIntegerField(help_text="Cover in km2")
    cape_town_cover = models.FloatField(help_text="In %")
    current_cape_town_area = models.FloatField(help_text="In km2")
    conserved_cape_town = models.PositiveSmallIntegerField(help_text="Conserved or managed, in km2")
    redlist = models.ForeignKey(Redlist, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255)
    spaces = models.ManyToManyField(ReferenceSpace, blank=True)

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

    @property
    def get_photo_medium(self):
        if self.photo:
            return self.photo.image.medium.url
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
    image = StdImageField(upload_to="photos", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)})
    position = models.PositiveSmallIntegerField(db_index=True, default=1)
    date = models.DateField(auto_now_add=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")
    species = models.ForeignKey(Species, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Photo {self.id}"

    class Meta:
        ordering = ["position"]

