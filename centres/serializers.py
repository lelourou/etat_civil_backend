from rest_framework import serializers
from django.db import models as db_models
from django.utils import timezone
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

    def validate(self, data):
        """
        R-Village — Un village ne peut appartenir qu'à un seul centre à une période donnée.
        Bloque la création si un rattachement actif existe déjà pour ce village.
        """
        # Uniquement en création (pas lors d'un PATCH de date_fin)
        if self.instance is not None:
            return data

        village = data.get('village')
        today   = timezone.now().date()

        conflit = RattachementVillage.objects.filter(
            village=village,
        ).filter(
            date_debut__lte=today,
        ).filter(
            db_models.Q(date_fin__isnull=True) | db_models.Q(date_fin__gt=today)
        ).exists()

        if conflit:
            raise serializers.ValidationError({
                'village': (
                    "Ce village est déjà rattaché à un centre actif. "
                    "Retirez-le d'abord de son centre actuel avant de le rattacher à un nouveau centre."
                )
            })
        return data
