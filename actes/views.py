from rest_framework import viewsets, filters, decorators, response, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Acte, MentionMarginale
from .serializers import (ActeSerializer, ActeCreateSerializer,
                           MentionMarginaleSerializer)
from .permissions import PeutGererActeDeCentre


class ActeViewSet(viewsets.ModelViewSet):
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nature', 'statut', 'centre', 'individu']
    search_fields    = ['numero_national', 'individu__nom', 'individu__prenoms',
                        'individu__nin']
    ordering_fields  = ['date_evenement', 'date_enregistrement', 'numero_national']

    def get_queryset(self):
        """
        R3/R4 — Filtrage par circonscription :
        - AGENT_GUICHET, SUPERVISEUR_CENTRE : liste limitée à leur centre.
          La consultation d'un acte individuel (retrieve) reste possible
          pour tous les centres authentifiés (lecture seule inter-centres).
        - SUPERVISEUR_NATIONAL, ADMIN_SYSTEME : accès à tout le système.
        """
        user = self.request.user
        qs = Acte.objects.select_related(
            'individu', 'centre', 'agent', 'superviseur', 'village'
        ).prefetch_related('mentions').all()

        if user.role in ['SUPERVISEUR_NATIONAL', 'ADMIN_SYSTEME']:
            return qs

        # Pour la liste, restreindre au centre de l'agent (R3)
        if self.action == 'list' and user.centre:
            return qs.filter(centre=user.centre)

        # Pour retrieve/detail, accès en lecture seule inter-centres (R4)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return ActeCreateSerializer
        return ActeSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [PeutGererActeDeCentre()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        R3 — L'acte est enregistré dans le centre de l'agent connecté.
             Les rôles SUPERVISEUR_NATIONAL et ADMIN_SYSTEME peuvent
             spécifier un autre centre via le champ 'centre' du payload.
        R5 — Après création d'un acte MARIAGE ou DECES, une notification
             inter-centres est automatiquement envoyée au centre qui a
             enregistré l'acte de naissance de l'individu.
        """
        user = self.request.user

        # R3 : forcer le centre pour les agents de terrain
        if user.role in ['AGENT_GUICHET', 'SUPERVISEUR_CENTRE']:
            acte = serializer.save(agent=user, centre=user.centre)
        else:
            acte = serializer.save(agent=user)

        # R5 : notification automatique mariage / décès inter-centres
        if acte.nature in [Acte.MARIAGE, Acte.DECES]:
            self._notifier_centre_naissance(acte)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _notifier_centre_naissance(self, acte):
        """
        R5 — Envoie une NotificationInterCentre au centre d'origine
        (celui qui a enregistré l'acte de naissance) lorsqu'un mariage
        ou un décès survient dans un autre centre.
        """
        from notifications.models import NotificationInterCentre

        individu       = acte.individu
        acte_naissance = Acte.objects.filter(
            individu=individu,
            nature=Acte.NAISSANCE,
        ).select_related('centre').first()

        # Pas de notification si même centre ou si naissance inconnue
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

    # ── Actions supplémentaires ───────────────────────────────────────────────

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
