from rest_framework import serializers
from food_via_trip.models import Location


class LocationSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('location_id', 'entity_id', 'entity_type', 'lat', 'long', 'address')