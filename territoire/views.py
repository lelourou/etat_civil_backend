from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Region, Departement, Localite, Village
from .serializers import RegionSerializer, DepartementSerializer, LocaliteSerializer, VillageSerializer


class RegionViewSet(viewsets.ModelViewSet):
    queryset         = Region.objects.all()
    serializer_class = RegionSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['nom', 'code']
    ordering_fields  = ['nom', 'created_at']


class DepartementViewSet(viewsets.ModelViewSet):
    queryset         = Departement.objects.select_related('region').all()
    serializer_class = DepartementSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['region']
    search_fields    = ['nom', 'code']


class LocaliteViewSet(viewsets.ModelViewSet):
    queryset         = Localite.objects.select_related('departement__region').all()
    serializer_class = LocaliteSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['departement', 'departement__region']
    search_fields    = ['nom', 'code']


class VillageViewSet(viewsets.ModelViewSet):
    queryset         = Village.objects.select_related('localite__departement').all()
    serializer_class = VillageSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['localite']
    search_fields    = ['nom', 'code']
