from django.db import models
from apps.common.models import SluggedContentModel, TimeStampedModel

class Person(SluggedContentModel):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    relationship = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=40, blank=True)
    biography = models.TextField(blank=True)
    organ_role = models.CharField(max_length=120, blank=True)

class Place(SluggedContentModel):
    location = models.CharField(max_length=255, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    historical_significance = models.TextField(blank=True)

class Institution(SluggedContentModel):
    founded_year = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=255, blank=True)

class TimelineEvent(TimeStampedModel):
    year = models.CharField(max_length=40)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, default="published")
    source = models.CharField(max_length=255, blank=True)
    related_item_ids = models.JSONField(default=list, blank=True)
