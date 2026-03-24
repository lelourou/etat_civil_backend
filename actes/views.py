from rest_framework import viewsets, filters, decorators, response, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Acte, MentionMarginale
from .serializers import (ActeSerializer, ActeCreateSerializer,
                           MentionMarginaleSerializer)
from .permissions import PeutGererActeDeCentre


class ActeViewSet(viewsets.ModelViewSet):
    queryset = Acte.objects.select_related(
        'individu', 'centre', 'agent', 'superviseur', 'village'
    ).prefetch_related('mentions').all()
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nature', 'statut', 'centre', 'individu']
    search_fields    = ['numero_national', 'individu__nom', 'individu__prenoms',
                        'individu__nin']
    ordering_fields  = ['date_evenement', 'date_enregistrement', 'numero_national']

    def get_serializer_class(self):
        if self.action == 'create':
            return ActeCreateSerializer
        return ActeSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [PeutGererActeDeCentre()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        acte = self.get_object()
        if acte.statut != Acte.BROUILLON:
            return response.Response(
                {"detail": "Seul un acte en brouillon peut être validé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        acte.valider(superviseur=request.user)
        return response.Response(ActeSerializer(acte).data)

    @decorators.action(detail=True, methods=['post'])
    def ajouter_mention(self, request, pk=None):
        acte = self.get_object()
        if acte.statut == Acte.VERROUILLE:
            return response.Response(
                {"detail": "Impossible de modifier un acte verrouillé."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = MentionMarginaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(acte=acte, agent=request.user)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['get'])
    def mentions(self, request, pk=None):
        acte      = self.get_object()
        mentions  = acte.mentions.all()
        serializer = MentionMarginaleSerializer(mentions, many=True)
        return response.Response(serializer.data)
