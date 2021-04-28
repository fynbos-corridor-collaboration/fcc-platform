from django.db import models
from stdimage.models import StdImageField
from django.utils.text import slugify
from markdown import markdown
from django.utils.safestring import mark_safe
from django.contrib.gis.db import models

class Page(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    image = StdImageField(upload_to="pages", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)})
    position = models.PositiveSmallIntegerField(db_index=True)
    slug = models.SlugField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["position"]

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

    content = models.TextField(null=True, blank=True)

class ReferenceSpace(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    photo = models.ForeignKey("Photo", on_delete=models.CASCADE, null=True, blank=True, related_name="referencespace")
    source = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, related_name="spaces")
    temp_source_id = models.IntegerField(null=True, blank=True, help_text="Only used when importing data")

    def __str__(self):
        return self.name

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

class Redlist(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Species(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    common_name = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    redlist = models.ForeignKey(Redlist, on_delete=models.CASCADE, null=True, blank=True)
    meta_data = models.JSONField(null=True, blank=True)
    links = models.JSONField(null=True, blank=True)
    animals = models.JSONField(null=True, blank=True)
    soils = models.JSONField(null=True, blank=True)
    properties = models.JSONField(null=True, blank=True)
    propagation_seed = models.TextField(null=True, blank=True)
    propagation_cutting = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    genus = models.ForeignKey(Genus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Photo(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    image = StdImageField(upload_to="photos", variations={"thumbnail": (350, 350), "medium": (800, 600), "large": (1280, 1024)})
    position = models.PositiveSmallIntegerField(db_index=True)
    date = models.DateField(auto_now_add=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")
    species = models.ForeignKey(Species, on_delete=models.CASCADE, null=True, blank=True, related_name="photos")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["position"]

