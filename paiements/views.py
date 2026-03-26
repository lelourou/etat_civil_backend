from rest_framework import viewsets, filters, decorators, response, status
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import DemandeCopie, Paiement
from .serializers import DemandeCopieSerializer, PaiementSerializer


class DemandeCopieViewSet(viewsets.ModelViewSet):
    serializer_class = DemandeCopieSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['statut', 'canal', 'type_copie']
    search_fields    = ['reference', 'demandeur_nom', 'acte__numero_national']

    def get_queryset(self):
        """R2 — Un AGENT_CENTRE ne voit que les demandes de son centre."""
        user = self.request.user
        qs = DemandeCopie.objects.select_related('acte', 'centre').prefetch_related('paiement').all()
        if user.role == 'AGENT_CENTRE' and user.centre:
            return qs.filter(centre=user.centre)
        return qs.none()

    @decorators.action(detail=True, methods=['post'])
    def confirmer_paiement(self, request, pk=None):
        demande = self.get_object()
        moyen   = request.data.get('moyen', 'ESPECES')
        ref_ext = request.data.get('reference_externe', '')
        if hasattr(demande, 'paiement') and demande.paiement.statut == Paiement.CONFIRME:
            return response.Response(
                {"detail": "Paiement déjà confirmé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        paiement, _ = Paiement.objects.get_or_create(demande=demande)
        paiement.moyen              = moyen
        paiement.statut             = Paiement.CONFIRME
        paiement.reference_externe  = ref_ext
        paiement.date_paiement      = timezone.now()
        paiement.recu_numero        = f"REC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        paiement.save()
        demande.statut = DemandeCopie.PAYEE
        demande.save()
        return response.Response(PaiementSerializer(paiement).data)
