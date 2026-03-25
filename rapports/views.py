from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta


ROLES_BI = ['SUPERVISEUR_CENTRE', 'SUPERVISEUR_NATIONAL', 'ADMIN_SYSTEME']


class RapportsMixin:
    """
    Retourne le filtre ORM adapté au rôle de l'utilisateur.
    - SUPERVISEUR_NATIONAL / ADMIN_SYSTEME : données nationales
    - SUPERVISEUR_CENTRE : données de son seul centre
    - Autres : accès refusé (None)
    """
    permission_classes = [IsAuthenticated]

    def get_filtre_actes(self, user):
        if user.role in ['SUPERVISEUR_NATIONAL', 'ADMIN_SYSTEME']:
            return {}
        if user.role == 'SUPERVISEUR_CENTRE' and user.centre:
            return {'centre': user.centre}
        return None

    def get_filtre_individus(self, user):
        if user.role in ['SUPERVISEUR_NATIONAL', 'ADMIN_SYSTEME']:
            return {}
        if user.role == 'SUPERVISEUR_CENTRE' and user.centre:
            return {'centre_naissance': user.centre}
        return None

    def get_filtre_paiements(self, user):
        if user.role in ['SUPERVISEUR_NATIONAL', 'ADMIN_SYSTEME']:
            return {}
        if user.role == 'SUPERVISEUR_CENTRE' and user.centre:
            return {'demande__centre': user.centre}
        return None

    def interdit(self, user):
        return user.role not in ROLES_BI


# ── 1. Synthèse (KPIs) ────────────────────────────────────────────────────────

class SyntheseView(RapportsMixin, APIView):
    """KPIs de synthèse : totaux globaux selon le rôle."""

    def get(self, request):
        from actes.models import Acte
        from paiements.models import Paiement
        from individus.models import Individu
        from notifications.models import NotificationInterCentre

        if self.interdit(request.user):
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        fa = self.get_filtre_actes(request.user)
        fi = self.get_filtre_individus(request.user)
        fp = self.get_filtre_paiements(request.user)

        total_actes     = Acte.objects.filter(**fa).count()
        actes_naissance = Acte.objects.filter(nature='NAISSANCE', **fa).count()
        actes_mariage   = Acte.objects.filter(nature='MARIAGE',   **fa).count()
        actes_deces     = Acte.objects.filter(nature='DECES',     **fa).count()
        actes_valides   = Acte.objects.filter(statut='VALIDE',    **fa).count()
        actes_brouillon = Acte.objects.filter(statut='BROUILLON', **fa).count()

        total_individus = Individu.objects.filter(**fi).count()
        individus_deces = Individu.objects.filter(est_decede=True, **fi).count()

        total_recettes = (
            Paiement.objects.filter(statut='CONFIRME', **fp)
            .aggregate(total=Sum('montant'))['total'] or 0
        )
        nb_paiements = Paiement.objects.filter(statut='CONFIRME', **fp).count()

        # Notifications : filtre sur centre_emetteur pour SUPERVISEUR_CENTRE
        fn = {}
        if request.user.role == 'SUPERVISEUR_CENTRE' and request.user.centre:
            fn = {'centre_emetteur': request.user.centre}
        total_notifications = NotificationInterCentre.objects.filter(**fn).count()
        notifs_attente = NotificationInterCentre.objects.filter(
            statut='EN_ATTENTE', **fn
        ).count()

        return Response({
            'total_actes':       total_actes,
            'actes_naissance':   actes_naissance,
            'actes_mariage':     actes_mariage,
            'actes_deces':       actes_deces,
            'actes_valides':     actes_valides,
            'actes_brouillon':   actes_brouillon,
            'total_individus':   total_individus,
            'individus_deces':   individus_deces,
            'total_recettes':    float(total_recettes),
            'nb_paiements':      nb_paiements,
            'total_notifications': total_notifications,
            'notifs_attente':    notifs_attente,
        })


# ── 2. Évolution mensuelle (12 derniers mois) ─────────────────────────────────

class EvolutionMensuelleView(RapportsMixin, APIView):
    """Nombre d'actes par mois et par nature sur les 12 derniers mois."""

    def get(self, request):
        from actes.models import Acte

        if self.interdit(request.user):
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        fa = self.get_filtre_actes(request.user)
        depuis = timezone.now() - timedelta(days=365)

        donnees = (
            Acte.objects.filter(date_enregistrement__gte=depuis, **fa)
            .annotate(mois=TruncMonth('date_enregistrement'))
            .values('mois', 'nature')
            .annotate(count=Count('id'))
            .order_by('mois', 'nature')
        )

        return Response([
            {
                'mois':   d['mois'].strftime('%Y-%m'),
                'nature': d['nature'],
                'count':  d['count'],
            }
            for d in donnees
        ])


# ── 3. Distribution par nature ────────────────────────────────────────────────

class ActesParNatureView(RapportsMixin, APIView):
    """Répartition des actes par nature (naissance / mariage / décès)."""

    def get(self, request):
        from actes.models import Acte

        if self.interdit(request.user):
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        fa = self.get_filtre_actes(request.user)
        donnees = (
            Acte.objects.filter(**fa)
            .values('nature')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response(list(donnees))


# ── 4. Top centres par volume d'actes ─────────────────────────────────────────

class ActesParCentreView(RapportsMixin, APIView):
    """Top 10 centres par nombre d'actes enregistrés."""

    def get(self, request):
        from actes.models import Acte

        if self.interdit(request.user):
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        fa = self.get_filtre_actes(request.user)
        donnees = (
            Acte.objects.filter(**fa)
            .values('centre__nom', 'centre__type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        return Response(list(donnees))


# ── 5. Recettes par centre ────────────────────────────────────────────────────

class RecettesParCentreView(RapportsMixin, APIView):
    """Montant total des recettes (droits de timbre) par centre."""

    def get(self, request):
        from paiements.models import Paiement

        if self.interdit(request.user):
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        fp = {**self.get_filtre_paiements(request.user), 'statut': 'CONFIRME'}
        donnees = (
            Paiement.objects.filter(**fp)
            .values('demande__centre__nom', 'demande__centre__type')
            .annotate(
                total=Sum('montant'),
                nb_paiements=Count('id'),
            )
            .order_by('-total')
        )
        return Response([
            {
                'centre_nom':    d['demande__centre__nom'],
                'centre_type':   d['demande__centre__type'],
                'total':         float(d['total']),
                'nb_paiements':  d['nb_paiements'],
            }
            for d in donnees
        ])


# ── 6. Paiements par canal et par moyen ───────────────────────────────────────

class PaiementsParCanalView(RapportsMixin, APIView):
    """Répartition des demandes de copie par canal (guichet / en ligne)
    et des paiements par moyen (espèces, MTN Money, Wave…)."""

    def get(self, request):
        from paiements.models import Paiement, DemandeCopie

        if self.interdit(request.user):
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        fd = {}
        if request.user.role == 'SUPERVISEUR_CENTRE' and request.user.centre:
            fd = {'centre': request.user.centre}

        par_canal = (
            DemandeCopie.objects.filter(**fd)
            .values('canal')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        fp = {**self.get_filtre_paiements(request.user), 'statut': 'CONFIRME'}
        par_moyen = (
            Paiement.objects.filter(**fp)
            .values('moyen')
            .annotate(count=Count('id'), total=Sum('montant'))
            .order_by('-count')
        )

        return Response({
            'par_canal': list(par_canal),
            'par_moyen': [
                {
                    'moyen': d['moyen'],
                    'count': d['count'],
                    'total': float(d['total']),
                }
                for d in par_moyen
            ],
        })
