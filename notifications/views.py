from rest_framework import viewsets, filters, decorators, response, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import NotificationInterCentre
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = NotificationInterCentre.objects.select_related(
        'acte_declencheur', 'centre_emetteur', 'centre_destinataire'
    ).all()
    serializer_class = NotificationSerializer
    filter_backends  = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['statut', 'type_evenement', 'centre_emetteur', 'centre_destinataire']
    ordering_fields  = ['created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPERVISEUR_NATIONAL':
            return super().get_queryset()
        if user.centre:
            return super().get_queryset().filter(centre_destinataire=user.centre)
        return super().get_queryset().none()

    @decorators.action(detail=True, methods=['post'])
    def acquitter(self, request, pk=None):
        notif = self.get_object()
        notif.acquitter()
        return response.Response(NotificationSerializer(notif).data)
