from rest_framework import serializers
from .models import DemandeCopie, Paiement


class PaiementSerializer(serializers.ModelSerializer):
    moyen_display  = serializers.CharField(source='get_moyen_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model  = Paiement
        fields = '__all__'
        read_only_fields = ['id', 'recu_numero', 'created_at']


class DemandeCopieSerializer(serializers.ModelSerializer):
    statut_display     = serializers.CharField(source='get_statut_display', read_only=True)
    canal_display      = serializers.CharField(source='get_canal_display', read_only=True)
    type_copie_display = serializers.CharField(source='get_type_copie_display', read_only=True)
    paiement           = PaiementSerializer(read_only=True)
    acte_numero        = serializers.CharField(source='acte.numero_national', read_only=True)

    class Meta:
        model  = DemandeCopie
        fields = '__all__'
        read_only_fields = ['id', 'reference', 'date_demande', 'created_at']
