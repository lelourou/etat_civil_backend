from rest_framework import viewsets, filters, decorators, response, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Individu, Filiation
from .serializers import IndividuSerializer, IndividuCreateSerializer, FiliationSerializer


class IndividuViewSet(viewsets.ModelViewSet):
    queryset = Individu.objects.select_related(
        'centre_naissance', 'lieu_naissance_village'
    ).prefetch_related('filiations').all()
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sexe', 'nationalite', 'est_decede', 'centre_naissance']
    search_fields    = ['nom', 'prenoms', 'nin']
    ordering_fields  = ['nom', 'prenoms', 'date_naissance']

    def get_serializer_class(self):
        if self.action == 'create':
            return IndividuCreateSerializer
        return IndividuSerializer

    @decorators.action(detail=False, methods=['post'])
    def verifier_doublon(self, request):
        nom              = request.data.get('nom', '')
        prenoms          = request.data.get('prenoms', '')
        date_naissance   = request.data.get('date_naissance', '')
        lieu_naissance   = request.data.get('lieu_naissance_libelle', '')
        doublon = Individu.verifier_doublon(nom, prenoms, date_naissance, lieu_naissance)
        if doublon:
            return response.Response({
                'doublon': True,
                'nin':     doublon.nin,
                'individu': IndividuSerializer(doublon).data,
            }, status=status.HTTP_200_OK)
        return response.Response({'doublon': False}, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['get'])
    def actes(self, request, pk=None):
        from actes.serializers import ActeSerializer
        individu = self.get_object()
        actes    = individu.actes.select_related('centre', 'agent').prefetch_related('mentions')
        serializer = ActeSerializer(actes, many=True)
        return response.Response(serializer.data)
