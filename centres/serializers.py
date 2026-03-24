from rest_framework import serializers
from .models import Centre, RattachementVillage


class CentreSerializer(serializers.ModelSerializer):
    localite_nom = serializers.CharField(source='localite.nom', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    nb_agents    = serializers.SerializerMethodField()

    class Meta:
        model  = Centre
        fields = '__all__'

    def get_nb_agents(self, obj):
        return obj.agents.filter(is_active=True).count()


class RattachementVillageSerializer(serializers.ModelSerializer):
    village_nom = serializers.CharField(source='village.nom', read_only=True)
    centre_nom  = serializers.CharField(source='centre.nom', read_only=True)
    est_courant = serializers.ReadOnlyField()

    class Meta:
        model  = RattachementVillage
        fields = '__all__'
