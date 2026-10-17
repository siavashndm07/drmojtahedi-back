from rest_framework import serializers
from apps.heritage.models import Person, Place, TimelineEvent


class PersonSerializer(serializers.ModelSerializer):
    organRole = serializers.CharField(source="organ_role", required=False, allow_blank=True)

    class Meta:
        model = Person
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "status",
            "source",
            "name",
            "role",
            "relationship",
            "kind",
            "biography",
            "organ_role",
            "organRole",
            "created_at",
            "updated_at",
        )


class PlaceSerializer(serializers.ModelSerializer):
    coordinates = serializers.SerializerMethodField()
    historicalSignificance = serializers.CharField(source="historical_significance", required=False, allow_blank=True)

    class Meta:
        model = Place
        fields = ("id","slug","title","description","status","source","location","lat","lng","coordinates","historical_significance","historicalSignificance","created_at","updated_at")

    def get_coordinates(self, obj):
        if obj.lat is None or obj.lng is None:
            return None
        return {"lat": obj.lat, "lng": obj.lng}

class TimelineEventSerializer(serializers.ModelSerializer):
    relatedItems = serializers.JSONField(source="related_item_ids", required=False)
    class Meta:
        model = TimelineEvent
        fields = ("id","year","title","description","location","category","status","source","related_item_ids","relatedItems","created_at","updated_at")
