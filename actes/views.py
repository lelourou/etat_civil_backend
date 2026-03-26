from rest_framework import viewsets, filters, decorators, response, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Acte, MentionMarginale
from .serializers import (ActeSerializer, ActeCreateSerializer,
                           MentionMarginaleSerializer)
from .permissions import EstAgentCentre, PeutGererActeDeCentre


class ActeViewSet(viewsets.ModelViewSet):
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nature', 'statut', 'individu']
    search_fields    = ['numero_national', 'individu__nom', 'individu__prenoms',
                        'individu__nin']
    ordering_fields  = ['date_evenement', 'date_enregistrement', 'numero_national']

    def get_queryset(self):
        """
        R2 — Un AGENT_CENTRE ne voit et ne gère que les actes de son centre.
        L'ADMIN_CENTRAL n'a pas accès aux actes.
        """
        user = self.request.user
        qs = Acte.objects.select_related(
            'individu', 'centre', 'agent', 'superviseur', 'village'
        ).prefetch_related('mentions').all()

        if user.centre:
            return qs.filter(centre=user.centre)
        return qs.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ActeCreateSerializer
        return ActeSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [PeutGererActeDeCentre()]
        return [EstAgentCentre()]

    def perform_create(self, serializer):
        """
        R2 — L'acte est enregistré dans le centre de l'agent connecté.
        R5 — Notification inter-centres déclenchée pour MARIAGE et DECES.
        """
        acte = serializer.save(agent=self.request.user, centre=self.request.user.centre)

        if acte.nature in [Acte.MARIAGE, Acte.DECES]:
            self._notifier_centre_naissance(acte)

    def _notifier_centre_naissance(self, acte):
        """
        R5 — Envoie une NotificationInterCentre au centre d'origine
        lorsqu'un mariage ou un décès survient dans un autre centre.
        """
        from notifications.models import NotificationInterCentre

        individu = acte.individu
        acte_naissance = Acte.objects.filter(
            individu=individu,
            nature=Acte.NAISSANCE,
        ).select_related('centre').first()

        if not acte_naissance or acte_naissance.centre == acte.centre:
            return

        NotificationInterCentre.objects.create(
            acte_declencheur    = acte,
            centre_emetteur     = acte.centre,
            centre_destinataire = acte_naissance.centre,
            acte_cible          = acte_naissance,
            type_evenement      = f'{acte.nature}_INTER_CENTRE',
            payload             = {
                'acte_id':          str(acte.id),
                'numero_national':  acte.numero_national,
                'individu_id':      str(individu.id),
                'individu_nom':     f"{individu.nom} {individu.prenoms}",
                'nature':           acte.nature,
                'date_evenement':   str(acte.date_evenement),
                'centre_evenement': acte.centre.code,
                'centre_naissance': acte_naissance.centre.code,
            },
        )

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
        mentions = self.get_object().mentions.all()
        return response.Response(MentionMarginaleSerializer(mentions, many=True).data)
