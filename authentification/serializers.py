from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Agent


class AgentSerializer(serializers.ModelSerializer):
    nom_complet  = serializers.ReadOnlyField()
    centre_nom   = serializers.CharField(source='centre.nom', read_only=True, default=None, allow_null=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model  = Agent
        fields = ['id', 'email', 'nom', 'prenoms', 'nom_complet', 'matricule',
                  'telephone', 'role', 'role_display', 'centre', 'centre_nom',
                  'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AgentCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12)

    class Meta:
        model  = Agent
        fields = ['email', 'nom', 'prenoms', 'matricule', 'telephone',
                  'role', 'centre', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        agent    = Agent(**validated_data)
        agent.set_password(password)
        agent.save()
        return agent


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)


class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['nom_complet'] = user.nom_complet
        token['role']        = user.role
        token['centre_id']   = str(user.centre_id) if user.centre_id else None
        token['centre_nom']  = user.centre.nom    if user.centre    else None
        token['centre_code'] = user.centre.code   if user.centre    else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Ajoute les infos agent dans la réponse login (en plus du token)
        data['agent'] = {
            'id':         str(self.user.id),
            'nom_complet': self.user.nom_complet,
            'role':        self.user.role,
            'centre_id':   str(self.user.centre_id) if self.user.centre_id else None,
            'centre_nom':  self.user.centre.nom     if self.user.centre    else None,
        }
        return data
