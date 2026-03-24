from rest_framework import serializers
from .models import Region, Departement, Localite, Village


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Region
        fields = '__all__'


class DepartementSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(source='region.nom', read_only=True)

    class Meta:
        model  = Departement
        fields = '__all__'


class LocaliteSerializer(serializers.ModelSerializer):
    departement_nom = serializers.CharField(source='departement.nom', read_only=True)
    region_nom      = serializers.CharField(source='departement.region.nom', read_only=True)

    class Meta:
        model  = Localite
        fields = '__all__'


class VillageSerializer(serializers.ModelSerializer):
    localite_nom = serializers.CharField(source='localite.nom', read_only=True)

    class Meta:
        model  = Village
        fields = '__all__'
