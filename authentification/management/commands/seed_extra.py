"""
Commande : python manage.py seed_extra
Complète la base avec les données manquantes :
décès, paiements, notifications.
Idempotente.
"""
import random, uuid
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

Agent = get_user_model()

NOMS = ['KOUASSI','KONAN','BAMBA','TRAORE','KONE','OUATTARA','DIALLO','COULIBALY',
        'YAPI','GOBA','AKRE','SEKA','TAPE','DJET','GNAGNE','ASSI','TOURE','FOFANA',
        'AHOUA','YEBOUE','BLE','SERI','GNEBA','LAGO','KOUA','AKA','YAO','KOFFI',
        'DIARRASSOUBA','MEITE','BAKAYOKO','SILUE','SANGARE','DOUMBIA']
PRENOMS = ['Jean','Aminata','Fatou','Moussa','Ibrahim','Siaka','Emmanuel','Christelle',
           'Kofi','Brice','Franck','Rosine','Mariam','Cynthia','Vanessa','Ghislain',
           'Adjoua','Yolande','Sylvie','Bintou','Estelle','Wilfried','Pauline']
CAUSES_DECES = ['Paludisme','Accident de la route','Maladie cardiovasculaire',
                'Causes naturelles','Hypertension artérielle','Diabète',
                'Septicémie','Insuffisance rénale','AVC','Cancer']
LIEUX_DECES = ['CHU de Yopougon','CHU de Cocody','Domicile','Clinique Sainte-Marie',
               'CHR de Daloa','Hôpital Général de Man','CHR de Bouaké']
MOYENS_PAI  = ['ESPECES','MTN_MONEY','ORANGE_MONEY','WAVE','VIREMENT']
CANAUX      = ['GUICHET','EN_LIGNE']
TYPES_COPIE = ['EXTRAIT','COPIE_INTEGRALE','BULLETIN']
STATUTS_DEM = ['EN_ATTENTE','TRAITE','LIVRE']


def rdate(y_min, y_max):
    start = date(y_min, 1, 1)
    end   = date(y_max, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


class Command(BaseCommand):
    help = "Ajoute les données manquantes (décès, paiements, notifications)"

    def handle(self, *args, **kwargs):
        self._deces()
        self._paiements()
        self._notifications()
        self._resume()

    # ── Actes de décès ────────────────────────────────────────────────────────

    def _deces(self):
        from actes.models import Acte, ActeDeces
        from individus.models import Individu
        from centres.models import Centre

        if Acte.objects.filter(nature=Acte.DECES).count() > 10:
            self.stdout.write("  Décès déjà présents — ignoré.")
            return

        admin   = Agent.objects.filter(role='ADMIN_CENTRAL').first()
        agents  = list(Agent.objects.filter(role='AGENT_CENTRE'))
        centres = list(Centre.objects.filter(actif=True))

        # Prendre des adultes non décédés
        pool = list(
            Individu.objects.filter(est_decede=False, date_naissance__year__lte=1995)
            .order_by('?')[:300]
        )

        cpt = {}
        nb  = 0

        for annee in range(2018, 2025):
            n_annee = random.randint(35, 50)
            for _ in range(n_annee):
                if not pool:
                    break
                ind    = pool.pop()
                centre = random.choice(centres)
                agent  = next((a for a in agents if a.centre_id == centre.id), admin)
                evt    = rdate(annee, annee)

                key = centre.code
                cpt[key] = cpt.get(key, 0) + 1
                num = f"D-{centre.code}-{annee}-{str(cpt[key]).zfill(5)}"

                acte = Acte(
                    nature=Acte.DECES,
                    statut=Acte.BROUILLON,
                    individu=ind,
                    centre=centre,
                    date_evenement=evt,
                    date_enregistrement=evt + timedelta(days=random.randint(1, 10)),
                    agent=agent,
                    numero_national=num,
                )
                if random.random() < 0.80:
                    acte.statut        = Acte.VALIDE
                    acte.superviseur   = admin
                    acte.date_validation = timezone.now()
                acte.save()

                ActeDeces.objects.create(
                    acte=acte,
                    heure_deces=f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
                    lieu_deces=random.choice(LIEUX_DECES),
                    cause_deces=random.choice(CAUSES_DECES),
                    declarant_nom=random.choice(NOMS),
                    declarant_prenoms=random.choice(PRENOMS),
                    declarant_lien=random.choice(['Fils','Fille','Époux','Épouse','Frère','Sœur']),
                    declarant_cin=f"CI{random.randint(100000,999999)}",
                )
                ind.est_decede = True
                ind.date_deces = evt
                ind.save(update_fields=['est_decede', 'date_deces'])
                nb += 1

        self.stdout.write(f"  {nb} actes de décès créés.")

    # ── Demandes de copie + paiements ─────────────────────────────────────────

    def _paiements(self):
        from actes.models import Acte
        from paiements.models import Paiement, DemandeCopie

        # Corriger les paiements créés avec un mauvais statut
        fixed = Paiement.objects.filter(statut='VALIDE').update(statut='CONFIRME')
        if fixed:
            self.stdout.write(f"  {fixed} paiements corrigés (VALIDE → CONFIRME).")

        if DemandeCopie.objects.count() > 10:
            self.stdout.write("  Demandes/paiements déjà présents — ignoré.")
            return

        actes_valides = list(
            Acte.objects.filter(statut=Acte.VALIDE).order_by('?')[:900]
        )
        montants = [500, 1000, 1000, 1500, 2000, 2000, 2500, 3000]
        nb_d = 0
        nb_p = 0

        for acte in actes_valides:
            d_evt = acte.date_evenement
            d_dem = d_evt + timedelta(days=random.randint(10, 730))
            # ne pas dépasser aujourd'hui
            if d_dem > date.today():
                d_dem = date.today() - timedelta(days=random.randint(1, 30))

            ref    = f"DEM-{uuid.uuid4().hex[:8].upper()}"
            canal  = random.choice(CANAUX)
            statut = random.choices(STATUTS_DEM, weights=[20, 40, 40])[0]

            demande = DemandeCopie.objects.create(
                reference=ref,
                acte=acte,
                demandeur_nom=random.choice(NOMS),
                demandeur_cin=f"CI{random.randint(100000,999999)}",
                demandeur_lien=random.choice(
                    ['Intéressé','Père','Mère','Fils','Fille','Employeur']),
                type_copie=random.choice(TYPES_COPIE),
                canal=canal,
                statut=statut,
                centre=acte.centre,
                date_demande=timezone.make_aware(
                    datetime(d_dem.year, d_dem.month, d_dem.day, random.randint(8,17), 0)
                ),
            )
            nb_d += 1

            if random.random() < 0.85:
                Paiement.objects.create(
                    demande=demande,
                    montant=random.choice(montants),
                    devise='FCFA',
                    moyen=random.choice(MOYENS_PAI),
                    statut='CONFIRME',
                    reference_externe=f"REF-{uuid.uuid4().hex[:10].upper()}",
                    date_paiement=timezone.make_aware(
                        datetime(d_dem.year, d_dem.month, d_dem.day, random.randint(8,17), 0)
                    ),
                    recu_numero=f"RECU-{str(nb_p+1).zfill(6)}",
                )
                nb_p += 1

        self.stdout.write(f"  {nb_d} demandes de copie + {nb_p} paiements créés.")

    # ── Notifications inter-centres ───────────────────────────────────────────

    def _notifications(self):
        from actes.models import Acte
        from notifications.models import NotificationInterCentre
        from centres.models import Centre

        if NotificationInterCentre.objects.count() > 10:
            self.stdout.write("  Notifications déjà présentes — ignoré.")
            return

        centres = list(Centre.objects.filter(actif=True))
        actes   = list(
            Acte.objects.filter(
                nature__in=[Acte.MARIAGE, Acte.DECES], statut=Acte.VALIDE
            ).order_by('?')[:150]
        )
        nb = 0

        for acte in actes:
            autres = [c for c in centres if c.id != acte.centre_id]
            if not autres:
                continue
            dest = random.choice(autres)
            NotificationInterCentre.objects.get_or_create(
                acte_declencheur=acte,
                centre_emetteur=acte.centre,
                centre_destinataire=dest,
                defaults={
                    'type_evenement': acte.nature,
                    'statut': random.choices(['ENVOYEE','ACQUITTEE'], weights=[40,60])[0],
                    'payload': {
                        'individu_nom': f"{acte.individu.nom} {acte.individu.prenoms}",
                        'nature': acte.nature,
                    },
                    'date_envoi': timezone.now(),
                }
            )
            nb += 1

        self.stdout.write(f"  {nb} notifications inter-centres créées.")

    # ── Résumé ────────────────────────────────────────────────────────────────

    def _resume(self):
        from actes.models import Acte
        from paiements.models import Paiement, DemandeCopie
        from notifications.models import NotificationInterCentre
        from individus.models import Individu

        self.stdout.write("\n  📊 État final de la base :")
        self.stdout.write(f"     Individus  : {Individu.objects.count()}")
        self.stdout.write(f"     Actes      : {Acte.objects.count()}")
        self.stdout.write(f"       Naissances : {Acte.objects.filter(nature='NAISSANCE').count()}")
        self.stdout.write(f"       Mariages   : {Acte.objects.filter(nature='MARIAGE').count()}")
        self.stdout.write(f"       Décès      : {Acte.objects.filter(nature='DECES').count()}")
        self.stdout.write(f"       Validés    : {Acte.objects.filter(statut='VALIDE').count()}")
        self.stdout.write(f"       Brouillons : {Acte.objects.filter(statut='BROUILLON').count()}")
        self.stdout.write(f"     Demandes   : {DemandeCopie.objects.count()}")
        self.stdout.write(f"     Paiements  : {Paiement.objects.count()}")
        self.stdout.write(f"     Notifs     : {NotificationInterCentre.objects.count()}")
