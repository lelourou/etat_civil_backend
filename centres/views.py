from rest_framework import viewsets, filters, decorators, response, status
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Centre, RattachementVillage
from .serializers import CentreSerializer, RattachementVillageSerializer


class CentreViewSet(viewsets.ModelViewSet):
    queryset         = Centre.objects.select_related('localite').all()
    serializer_class = CentreSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'actif', 'localite']
    search_fields    = ['nom', 'code']
    ordering_fields  = ['nom', 'date_creation']

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


# Fix missing import
from django.db import models
