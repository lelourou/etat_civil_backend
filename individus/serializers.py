from rest_framework import serializers
from .models import Individu, Filiation


class FiliationSerializer(serializers.ModelSerializer):
    role_display      = serializers.CharField(source='get_role_display', read_only=True)
    parent_nom_complet = serializers.SerializerMethodField()

    class Meta:
        model  = Filiation
        fields = '__all__'

    def get_parent_nom_complet(self, obj):
        if obj.parent:
            return f"{obj.parent.nom} {obj.parent.prenoms}"
        return f"{obj.nom_libelle} {obj.prenoms_libelle}".strip()


class IndividuSerializer(serializers.ModelSerializer):
    sexe_display            = serializers.CharField(source='get_sexe_display', read_only=True)
    centre_naissance_nom    = serializers.CharField(source='centre_naissance.nom', read_only=True)
    lieu_naissance_village_nom = serializers.CharField(source='lieu_naissance_village.nom',
                                                        read_only=True)
    filiations              = FiliationSerializer(many=True, read_only=True)

    class Meta:
        model  = Individu
        fields = '__all__'
        read_only_fields = ['id', 'nin', 'hash_biographique', 'est_decede',
                             'date_deces', 'created_at', 'updated_at']


class IndividuCreateSerializer(serializers.ModelSerializer):
    filiations = FiliationSerializer(many=True, required=False)

    class Meta:
        model  = Individu
        fields = ['nom', 'prenoms', 'sexe', 'date_naissance', 'lieu_naissance_village',
                  'lieu_naissance_libelle', 'nationalite', 'centre_naissance', 'filiations']

    def validate(self, data):
        doublon = Individu.verifier_doublon(
            data['nom'], data['prenoms'], data['date_naissance'],
            data.get('lieu_naissance_libelle', '')
        )
        if doublon:
            raise serializers.ValidationError(
                f"DOUBLON_DETECTE: Un individu similaire existe déjà. NIN: {doublon.nin}"
            )
        return data

    def create(self, validated_data):
        filiations_data = validated_data.pop('filiations', [])
        individu = Individu.objects.create(**validated_data)
        # Générer NIN
        individu.nin = f"CI{str(individu.created_at.year)}{str(individu.pk)[:8].upper()}"
        individu.save(update_fields=['nin'])
        for f in filiations_data:
            Filiation.objects.create(enfant=individu, **f)
        return individu
