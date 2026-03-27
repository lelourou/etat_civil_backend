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

        # R-DECES — Individu décédé ne peut plus avoir de nouveaux actes sauf décès
        if individu and individu.est_decede and nature != Acte.DECES:
            raise serializers.ValidationError(
                "Impossible de créer un acte pour un individu décédé."
            )

        if individu and nature:
            # R-NAISSANCE — Un seul acte de naissance par individu (national + local)
            if nature == Acte.NAISSANCE:
                if Acte.objects.filter(individu=individu, nature=Acte.NAISSANCE).exists():
                    raise serializers.ValidationError(
                        "Un acte de naissance existe déjà pour cet individu "
                        "dans la base nationale."
                    )

            # R-DECES — Un seul acte de décès par individu
            if nature == Acte.DECES:
                if Acte.objects.filter(individu=individu, nature=Acte.DECES).exists():
                    raise serializers.ValidationError(
                        "Un acte de décès existe déjà pour cet individu."
                    )

            # R-MARIAGE — Pas de remariage sans divorce préalable
            if nature == Acte.MARIAGE:
                dernier_mariage = (
                    Acte.objects
                    .filter(individu=individu, nature=Acte.MARIAGE)
                    .order_by('-date_evenement')
                    .first()
                )
                if dernier_mariage:
                    a_divorce = dernier_mariage.mentions.filter(
                        type_mention=MentionMarginale.DIVORCE
                    ).exists()
                    if not a_divorce:
                        raise serializers.ValidationError(
                            "Cet individu est déjà marié(e). Un acte de divorce doit "
                            "être enregistré (mention marginale DIVORCE) avant "
                            "tout nouveau mariage."
                        )

                # Vérifier aussi pour l'époux/épouse si fournis dans detail_mariage
                detail = data.get('detail_mariage', {})
                for role_field in ['epoux', 'epouse']:
                    conjoint = detail.get(role_field) if isinstance(detail, dict) else getattr(detail, role_field, None)
                    if conjoint and conjoint != individu:
                        dernier = (
                            Acte.objects
                            .filter(individu=conjoint, nature=Acte.MARIAGE)
                            .order_by('-date_evenement')
                            .first()
                        )
                        if dernier:
                            a_div = dernier.mentions.filter(
                                type_mention=MentionMarginale.DIVORCE
                            ).exists()
                            if not a_div:
                                raise serializers.ValidationError(
                                    f"Le/la {role_field} est déjà marié(e). "
                                    "Un divorce doit être enregistré avant ce mariage."
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
