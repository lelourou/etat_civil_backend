from rest_framework import serializers
from .models import Acte, ActeNaissance, ActeMariage, ActeDeces, MentionMarginale


class ActeNaissanceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ActeNaissance
        exclude = ['acte']


class ActeMariageSerializer(serializers.ModelSerializer):
    epoux_nom  = serializers.CharField(source='epoux.nom_complet', read_only=True)
    epouse_nom = serializers.CharField(source='epouse.nom_complet', read_only=True)

    class Meta:
        model  = ActeMariage
        exclude = ['acte']


class ActeDecesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ActeDeces
        exclude = ['acte']


class MentionMarginaleSerializer(serializers.ModelSerializer):
    type_mention_display = serializers.CharField(source='get_type_mention_display', read_only=True)
    agent_nom            = serializers.CharField(source='agent.nom_complet', read_only=True)

    class Meta:
        model  = MentionMarginale
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'agent']


class ActeSerializer(serializers.ModelSerializer):
    nature_display  = serializers.CharField(source='get_nature_display', read_only=True)
    statut_display  = serializers.CharField(source='get_statut_display', read_only=True)
    individu_nom    = serializers.SerializerMethodField()
    centre_nom      = serializers.CharField(source='centre.nom', read_only=True)
    agent_nom       = serializers.CharField(source='agent.nom_complet', read_only=True)
    mentions        = MentionMarginaleSerializer(many=True, read_only=True)
    detail_naissance = ActeNaissanceSerializer(read_only=True)
    detail_mariage   = ActeMariageSerializer(read_only=True)
    detail_deces     = ActeDecesSerializer(read_only=True)

    class Meta:
        model  = Acte
        fields = '__all__'
        read_only_fields = ['id', 'numero_national', 'date_enregistrement',
                             'agent', 'superviseur', 'date_validation',
                             'hash_contenu', 'created_at', 'updated_at']

    def get_individu_nom(self, obj):
        return f"{obj.individu.nom} {obj.individu.prenoms}"


class ActeCreateSerializer(serializers.ModelSerializer):
    detail_naissance = ActeNaissanceSerializer(required=False)
    detail_mariage   = ActeMariageSerializer(required=False)
    detail_deces     = ActeDecesSerializer(required=False)

    class Meta:
        model  = Acte
        fields = ['nature', 'individu', 'centre', 'village', 'date_evenement',
                  'observations', 'detail_naissance', 'detail_mariage', 'detail_deces']

    def validate(self, data):
        individu = data.get('individu')
        nature   = data.get('nature')
        if individu and individu.est_decede and nature != Acte.DECES:
            raise serializers.ValidationError(
                "Impossible de créer un acte pour un individu décédé."
            )
        return data

    def create(self, validated_data):
        naissance_data = validated_data.pop('detail_naissance', None)
        mariage_data   = validated_data.pop('detail_mariage', None)
        deces_data     = validated_data.pop('detail_deces', None)
        acte = Acte.objects.create(**validated_data)
        if naissance_data and acte.nature == Acte.NAISSANCE:
            ActeNaissance.objects.create(acte=acte, **naissance_data)
        if mariage_data and acte.nature == Acte.MARIAGE:
            ActeMariage.objects.create(acte=acte, **mariage_data)
        if deces_data and acte.nature == Acte.DECES:
            ActeDeces.objects.create(acte=acte, **deces_data)
        return acte
