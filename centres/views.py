from rest_framework import viewsets, filters, decorators, response, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.utils import timezone
from .models import Centre, RattachementVillage
from .serializers import CentreSerializer, RattachementVillageSerializer


class EstAdminCentral(IsAuthenticated):
    """Seul un ADMIN_CENTRAL peut créer/modifier/supprimer des centres."""
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == 'ADMIN_CENTRAL'
        )


class CentreViewSet(viewsets.ModelViewSet):
    queryset         = Centre.objects.select_related('localite').all()
    serializer_class = CentreSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'actif', 'localite']
    search_fields    = ['nom', 'code']
    ordering_fields  = ['nom', 'date_creation']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EstAdminCentral()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        R2 — Règle de gestion : une sous-préfecture ACTIVE doit exister
        dans la même localité avant de pouvoir créer une mairie.
        """
        localite    = serializer.validated_data.get('localite')
        type_centre = serializer.validated_data.get('type')

        if type_centre == Centre.MAIRIE:
            sous_pref_existe = Centre.objects.filter(
                localite=localite,
                type=Centre.SOUS_PREFECTURE,
                actif=True,
            ).exists()
            if not sous_pref_existe:
                raise ValidationError({
                    'type': (
                        "R2 — Une sous-préfecture active doit exister dans cette localité "
                        "avant de créer une mairie."
                    )
                })
        serializer.save()

    @decorators.action(detail=True, methods=['get'])
    def villages_courants(self, request, pk=None):
        centre = self.get_object()
        today  = timezone.now().date()
        rattachements = RattachementVillage.objects.filter(
            centre=centre
        ).filter(
            date_debut__lte=today
        ).filter(
            models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=today)
        ).select_related('village')
        serializer = RattachementVillageSerializer(rattachements, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=['get'])
    def agents(self, request, pk=None):
        from authentification.serializers import AgentSerializer
        centre = self.get_object()
        agents = centre.agents.filter(is_active=True)
        serializer = AgentSerializer(agents, many=True)
        return response.Response(serializer.data)


class RattachementVillageViewSet(viewsets.ModelViewSet):
    queryset         = RattachementVillage.objects.select_related('village', 'centre').all()
    serializer_class = RattachementVillageSerializer
    filter_backends  = [DjangoFilterBackend]
    filterset_fields = ['village', 'centre']
