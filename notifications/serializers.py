from rest_framework import serializers
from .models import NotificationInterCentre


class NotificationSerializer(serializers.ModelSerializer):
    statut_display          = serializers.CharField(source='get_statut_display', read_only=True)
    centre_emetteur_nom     = serializers.CharField(source='centre_emetteur.nom', read_only=True)
    centre_destinataire_nom = serializers.CharField(source='centre_destinataire.nom', read_only=True)
    acte_numero             = serializers.CharField(source='acte_declencheur.numero_national',
                                                    read_only=True)

    class Meta:
        model  = NotificationInterCentre
        fields = '__all__'
        read_only_fields = ['id', 'tentatives', 'date_envoi', 'date_acquittement', 'created_at']
