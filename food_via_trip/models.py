from __future__ import unicode_literals

from django.db import models
import uuid


# Create your models here.

class Location(models.Model):
    location_id = models.CharField(max_length=255, unique=True, blank=False)
    entity_id = models.IntegerField()
    entity_type = models.CharField(max_length=20)
    lat = models.FloatField()
    long = models.FloatField()
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.address
