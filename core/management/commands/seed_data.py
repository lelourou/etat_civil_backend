"""
Commande de génération de données statistiques réalistes pour le mémoire SID M2.
Volume : ~1 200 individus | ~1 800 actes (2020-2025) | ~800 paiements
Patterns : saisonnalité, gradient urbain/rural, anomalies pour détection de fraude.

Usage : python manage.py seed_data [--clear]
"""
import random
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from territoire.models   import Region, Departement, Localite, Village
from centres.models      import Centre, RattachementVillage
from authentification.models import Agent
from individus.models    import Individu, Filiation
from actes.models        import Acte, ActeNaissance, ActeMariage, ActeDeces, MentionMarginale
from paiements.models    import DemandeCopie, Paiement
from notifications.models import NotificationInterCentre


# ─────────────────────────────────────────────────────────────────────────────
# 1.  DONNÉES GÉOGRAPHIQUES — couverture nationale Côte d'Ivoire
# ─────────────────────────────────────────────────────────────────────────────

REGIONS = [
    ('RG-AB', 'Abidjan'),
    ('RG-LA', 'Lagunes'),
    ('RG-GD', 'Gôh-Djiboua'),
    ('RG-SS', 'Sassandra-Marahoué'),
    ('RG-VB', 'Vallée du Bandama'),
    ('RG-ZZ', 'Zanzan'),
    ('RG-WR', 'Woroba'),
    ('RG-MO', 'Montagnes'),
    ('RG-CO', 'Comoé'),
    ('RG-LS', 'Lacs'),
]

DEPARTEMENTS = [
    # Abidjan
    ('DP-CO', 'Cocody',        'RG-AB'),
    ('DP-PL', 'Plateau',       'RG-AB'),
    ('DP-YO', 'Yopougon',      'RG-AB'),
    ('DP-AB', 'Abobo',         'RG-AB'),
    ('DP-AC', 'Adjamé',        'RG-AB'),
    ('DP-PA', 'Port-Bouët',    'RG-AB'),
    # Lagunes
    ('DP-JA', 'Jacqueville',   'RG-LA'),
    ('DP-DA', 'Dabou',         'RG-LA'),
    ('DP-GR', 'Grand-Lahou',   'RG-LA'),
    # Gôh-Djiboua
    ('DP-DI', 'Divo',          'RG-GD'),
    ('DP-HI', 'Hiré',          'RG-GD'),
    # Sassandra-Marahoué
    ('DP-DG', 'Daloa',         'RG-SS'),
    ('DP-IS', 'Issia',         'RG-SS'),
    # Vallée du Bandama
    ('DP-BK', 'Bouaké',        'RG-VB'),
    ('DP-SK', 'Sakassou',      'RG-VB'),
    # Zanzan
    ('DP-BD', 'Bondoukou',     'RG-ZZ'),
    ('DP-TZ', 'Tanda',         'RG-ZZ'),
    # Woroba
    ('DP-SE', 'Séguéla',       'RG-WR'),
    # Montagnes
    ('DP-MN', 'Man',           'RG-MO'),
    # Comoé
    ('DP-AB2','Abengourou',    'RG-CO'),
    # Lacs
    ('DP-DM', 'Dimbokro',      'RG-LS'),
]

LOCALITES = [
    ('LC-CO1', 'Cocody-Riviera',    'DP-CO'),
    ('LC-CO2', 'Cocody-2 Plateaux', 'DP-CO'),
    ('LC-PL1', 'Plateau-Centre',    'DP-PL'),
    ('LC-YO1', 'Yopougon-Selmer',   'DP-YO'),
    ('LC-YO2', 'Yopougon-Maroc',    'DP-YO'),
    ('LC-AB1', 'Abobo-Centre',      'DP-AB'),
    ('LC-AB2', 'Abobo-Gare',        'DP-AB'),
    ('LC-AC1', 'Adjamé-Liberté',    'DP-AC'),
    ('LC-PA1', 'Port-Bouët-Centre', 'DP-PA'),
    ('LC-JA1', 'Jacqueville-Centre','DP-JA'),
    ('LC-DA1', 'Dabou-Centre',      'DP-DA'),
    ('LC-GR1', 'Grand-Lahou-Centre','DP-GR'),
    ('LC-DI1', 'Divo-Centre',       'DP-DI'),
    ('LC-HI1', 'Hiré-Centre',       'DP-HI'),
    ('LC-DG1', 'Daloa-Centre',      'DP-DG'),
    ('LC-IS1', 'Issia-Centre',      'DP-IS'),
    ('LC-BK1', 'Bouaké-Nord',       'DP-BK'),
    ('LC-SK1', 'Sakassou-Centre',   'DP-SK'),
    ('LC-BD1', 'Bondoukou-Centre',  'DP-BD'),
    ('LC-TZ1', 'Tanda-Centre',      'DP-TZ'),
    ('LC-SE1', 'Séguéla-Centre',    'DP-SE'),
    ('LC-MN1', 'Man-Centre',        'DP-MN'),
    ('LC-AB3', 'Abengourou-Centre', 'DP-AB2'),
    ('LC-DM1', 'Dimbokro-Centre',   'DP-DM'),
]

VILLAGES = [
    ('VL-001', 'Riviera 2',          'LC-CO1'),
    ('VL-002', 'Riviera Palmeraie',  'LC-CO1'),
    ('VL-003', 'Cocody-Danga',       'LC-CO2'),
    ('VL-004', 'Plateau-Akwaba',     'LC-PL1'),
    ('VL-005', 'Selmer Village',     'LC-YO1'),
    ('VL-006', 'Maroc-Centre',       'LC-YO2'),
    ('VL-007', 'Abobo-Baoulé',       'LC-AB1'),
    ('VL-008', 'Gare-Nord',          'LC-AB2'),
    ('VL-009', 'Liberté-3',          'LC-AC1'),
    ('VL-010', 'Port-Bouët-Vridi',   'LC-PA1'),
    ('VL-011', 'Jacqueville-Plage',  'LC-JA1'),
    ('VL-012', 'Dabou-Lagune',       'LC-DA1'),
    ('VL-013', 'Grand-Lahou-Plage',  'LC-GR1'),
    ('VL-014', 'Divo-Marché',        'LC-DI1'),
    ('VL-015', 'Hiré-Mine',          'LC-HI1'),
    ('VL-016', 'Daloa-Tazibouo',     'LC-DG1'),
    ('VL-017', 'Issia-Centre',       'LC-IS1'),
    ('VL-018', 'Bouaké-Bromakoté',   'LC-BK1'),
    ('VL-019', 'Sakassou-Village',   'LC-SK1'),
    ('VL-020', 'Bondoukou-Zanzan',   'LC-BD1'),
    ('VL-021', 'Tanda-Village',      'LC-TZ1'),
    ('VL-022', 'Séguéla-Worodougou', 'LC-SE1'),
    ('VL-023', 'Man-Tounwrou',       'LC-MN1'),
    ('VL-024', 'Abengourou-Est',     'LC-AB3'),
    ('VL-025', 'Dimbokro-Centre',    'LC-DM1'),
]

# Centres avec poids de volume pour simuler gradient urbain/rural
# (code, nom, type, localite_code, poids_volume)
CENTRES_DATA = [
    # ── Abidjan – urbain dense ──────────────────────────────────────────────
    ('CTR-CO1', 'Sous-Préfecture de Cocody',          'SOUS_PREFECTURE', 'LC-CO1', 18),
    ('CTR-PL1', 'Mairie du Plateau',                  'MAIRIE',          'LC-PL1', 16),
    ('CTR-YO1', 'Sous-Préfecture de Yopougon',        'SOUS_PREFECTURE', 'LC-YO1', 20),
    ('CTR-AB1', 'Mairie d\'Abobo',                    'MAIRIE',          'LC-AB1', 17),
    ('CTR-AC1', 'Sous-Préfecture d\'Adjamé',          'SOUS_PREFECTURE', 'LC-AC1', 14),
    ('CTR-PA1', 'Mairie de Port-Bouët',               'MAIRIE',          'LC-PA1', 12),
    # ── Lagunes / zone côtière ──────────────────────────────────────────────
    ('CTR-JA1', 'Sous-Préfecture de Jacqueville',     'SOUS_PREFECTURE', 'LC-JA1',  5),
    ('CTR-DA1', 'Mairie de Dabou',                    'MAIRIE',          'LC-DA1',  8),
    ('CTR-GR1', 'Sous-Préfecture de Grand-Lahou',     'SOUS_PREFECTURE', 'LC-GR1',  4),
    # ── Centre-Ouest ────────────────────────────────────────────────────────
    ('CTR-DI1', 'Sous-Préfecture de Divo',            'SOUS_PREFECTURE', 'LC-DI1', 10),
    ('CTR-HI1', 'Mairie de Hiré',                     'MAIRIE',          'LC-HI1',  4),
    ('CTR-DG1', 'Sous-Préfecture de Daloa',           'SOUS_PREFECTURE', 'LC-DG1', 11),
    ('CTR-IS1', 'Mairie d\'Issia',                    'MAIRIE',          'LC-IS1',  5),
    # ── Centre ──────────────────────────────────────────────────────────────
    ('CTR-BK1', 'Sous-Préfecture de Bouaké',          'SOUS_PREFECTURE', 'LC-BK1', 13),
    ('CTR-SK1', 'Mairie de Sakassou',                 'MAIRIE',          'LC-SK1',  3),
    # ── Est ─────────────────────────────────────────────────────────────────
    ('CTR-BD1', 'Sous-Préfecture de Bondoukou',       'SOUS_PREFECTURE', 'LC-BD1',  7),
    ('CTR-TZ1', 'Mairie de Tanda',                    'MAIRIE',          'LC-TZ1',  4),
    # ── Ouest / Nord-Ouest ──────────────────────────────────────────────────
    ('CTR-SE1', 'Sous-Préfecture de Séguéla',         'SOUS_PREFECTURE', 'LC-SE1',  5),
    ('CTR-MN1', 'Sous-Préfecture de Man',             'SOUS_PREFECTURE', 'LC-MN1',  8),
    # ── Sud-Est / Centre-Est ────────────────────────────────────────────────
    ('CTR-AB3', 'Sous-Préfecture d\'Abengourou',      'SOUS_PREFECTURE', 'LC-AB3',  6),
    ('CTR-DM1', 'Mairie de Dimbokro',                 'MAIRIE',          'LC-DM1',  5),
]

# ─────────────────────────────────────────────────────────────────────────────
# 2.  RÉFÉRENTIELS NOMINAUX IVOIRIENS
# ─────────────────────────────────────────────────────────────────────────────

NOMS = [
    'KOUAME', 'KONAN', 'KOFFI', 'YAO', 'BROU', 'ASSI', 'AHOUA', 'AHORE',
    'GNAGNE', 'TAPE', 'PEHE', 'DAHO', 'GUEHI', 'BLE',
    'TRAORE', 'COULIBALY', 'DIALLO', 'BAMBA', 'TOURE', 'OUATTARA',
    'KONE', 'CAMARA', 'DIOMANDE', 'SANGARE', 'CISSE', 'FOFANA', 'DOUMBIA',
    'GBAGBO', 'GUEDE', 'LAGO', 'LORNG', 'GOIN', 'WE', 'TRE',
    'KOUASSI', 'N\'GUESSAN', 'N\'DRI', 'N\'ZI', 'BOKA', 'ETTIEN',
]

PRENOMS_M = [
    'Jean', 'Paul', 'Pierre', 'Jacques', 'Henri', 'René', 'Marcel',
    'Kouadio', 'Kofi', 'Koffi', 'Yao', 'Kouassi', 'Kouakou', 'N\'Goran',
    'Amara', 'Mamadou', 'Ibrahim', 'Moussa', 'Issouf', 'Hamadou',
    'Adama', 'Seydou', 'Aboubacar', 'Drissa', 'Souleymane', 'Lacina',
    'Maxime', 'Franck', 'Didier', 'Serge', 'Eric', 'Martial', 'Brice',
    'Rodrigue', 'Wilfried', 'Stéphane', 'Aristide', 'Ghislain',
]

PRENOMS_F = [
    'Marie', 'Aïcha', 'Fatou', 'Aminata', 'Mariam', 'Hawa', 'Djeneba',
    'Adjoua', 'Akissi', 'Affoue', 'Amenan', 'Assata', 'Yawa', 'Akua',
    'Fatoumata', 'Salimata', 'Rokia', 'Bintou', 'Ramata', 'Awa',
    'Aya', 'Chantal', 'Estelle', 'Nadège', 'Sandrine', 'Clémentine',
    'Geneviève', 'Thérèse', 'Joëlle', 'Patricia', 'Danielle',
]

LIEUX_NAISSANCE = [
    'Abidjan', 'Bouaké', 'Daloa', 'Korhogo', 'San-Pédro',
    'Yamoussoukro', 'Divo', 'Man', 'Gagnoa', 'Abengourou',
    'Bondoukou', 'Dabou', 'Jacqueville', 'Agboville', 'Adzopé',
    'Séguéla', 'Dimbokro', 'Mankono', 'Touba', 'Odienné',
]

HOPITAUX = [
    'CHU de Cocody', 'CHU de Treichville', 'CHU de Yopougon',
    'Clinique Sainte Marie', 'Maternité centrale d\'Abidjan',
    'CHR de Bouaké', 'CHR de Daloa', 'CHR de Man',
    'Hôpital Général de Divo', 'Maternité de Port-Bouët',
    'Centre de Santé de Dabou', '', '',  # vides = accouchement à domicile
]

CAUSES_DECES = [
    'Paludisme', 'Insuffisance cardiaque', 'Accident de la route',
    'Diabète', 'Hypertension artérielle', 'Cancer', 'Vieillesse',
    'Pneumonie', 'Septicémie', '', '',
]

# ─────────────────────────────────────────────────────────────────────────────
# 3.  PATTERNS SAISONNIERS (pour séries temporelles)
#     Basés sur des estimations réalistes CI
# ─────────────────────────────────────────────────────────────────────────────

# Naissances : pic en jan-fév (conceptions mars-avr) et juil-août
NAISSANCE_WEIGHT = [1.25, 1.30, 1.10, 0.95, 0.90, 0.85, 1.10, 1.15, 0.95, 0.85, 0.85, 0.95]
# Mariages : pic en déc-jan (fêtes) et août
MARIAGE_WEIGHT   = [1.30, 0.90, 0.80, 0.80, 0.85, 0.90, 0.90, 1.10, 0.90, 0.85, 0.90, 1.40]
# Décès : légèrement plus élevé en saison sèche (nov-avr) — paludisme, méningite
DECES_WEIGHT     = [1.15, 1.10, 1.10, 1.05, 0.90, 0.85, 0.85, 0.85, 0.90, 0.95, 1.10, 1.20]

# Tendance annuelle linéaire (+5 % / an car montée en charge du système)
TREND_YEAR_BASE  = 2020


def appliquer_poids_mensuel(annee, mois, poids_mensuel):
    """Retourne True si on génère un acte ce mois selon le poids saisonnier."""
    return random.random() < poids_mensuel[mois - 1]


def date_aleatoire(annee, mois, poids_mensuel):
    """Tire une date dans le mois avec respect de la saisonnalité."""
    dernier_jour = [31,28,31,30,31,30,31,31,30,31,30,31][mois-1]
    if annee % 4 == 0 and mois == 2:
        dernier_jour = 29
    return datetime.date(annee, mois, random.randint(1, dernier_jour))


# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Génère des données statistiques réalistes pour le mémoire SID M2 CI'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Supprimer toutes les données existantes avant de générer')
        parser.add_argument('--individus', type=int, default=1200,
                            help='Nombre d\'individus à générer (défaut : 1200)')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== Génération des données statistiques État Civil CI — Mémoire SID M2 ===\n'
        ))

        self._creer_territoire()
        centres   = self._creer_centres()
        agents    = self._creer_agents(centres)
        individus = self._creer_individus(centres, nb=options['individus'])
        actes     = self._creer_actes(agents, individus, centres)
        self._creer_paiements(actes, centres)
        self._creer_mentions(actes, agents)
        self._creer_notifications(actes, centres)

        self.stdout.write(self.style.SUCCESS('\n✅ Données générées avec succès !\n'))
        self._afficher_resume()

    # ─── Clear ────────────────────────────────────────────────────────────────

    def _clear_data(self):
        for m in [NotificationInterCentre, Paiement, DemandeCopie,
                  MentionMarginale, ActeNaissance, ActeMariage, ActeDeces,
                  Acte, Filiation, Individu]:
            m.objects.all().delete()
        Agent.objects.filter(is_superuser=False).delete()
        for m in [RattachementVillage, Centre, Village, Localite, Departement, Region]:
            m.objects.all().delete()

    # ─── Territoire ───────────────────────────────────────────────────────────

    def _creer_territoire(self):
        self.stdout.write('📍 Création du territoire (10 régions, 21 dpts, 24 localités)...')

        regions = {}
        for code, nom in REGIONS:
            r, _ = Region.objects.get_or_create(code=code, defaults={'nom': nom})
            regions[code] = r

        departements = {}
        for code, nom, reg in DEPARTEMENTS:
            d, _ = Departement.objects.get_or_create(
                code=code, defaults={'nom': nom, 'region': regions[reg]}
            )
            departements[code] = d

        localites = {}
        for code, nom, dept in LOCALITES:
            l, _ = Localite.objects.get_or_create(
                code=code, defaults={'nom': nom, 'departement': departements[dept]}
            )
            localites[code] = l

        villages = {}
        for code, nom, loc in VILLAGES:
            v, _ = Village.objects.get_or_create(
                code=code, defaults={'nom': nom, 'localite': localites[loc]}
            )
            villages[code] = v

        self.stdout.write(f'   ✓ {len(regions)} régions · {len(departements)} départements · '
                          f'{len(localites)} localités · {len(villages)} villages')

    # ─── Centres ──────────────────────────────────────────────────────────────

    def _creer_centres(self):
        self.stdout.write('🏛️  Création des 21 centres (SP + Mairies)...')

        localites = {l.code: l for l in Localite.objects.all()}
        centres   = {}

        for code, nom, type_c, loc_code, _ in CENTRES_DATA:
            c, _ = Centre.objects.get_or_create(
                code=code,
                defaults={
                    'nom': nom,
                    'type': type_c,
                    'localite': localites[loc_code],
                    'date_creation': datetime.date(2010, 1, 1),
                    'telephone': f'+225 27 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99):02d}',
                    'email': f'{code.lower().replace("-",".")}@etatcivil.ci',
                }
            )
            centres[code] = c

        # Rattachements village → centre (round-robin)
        villages = list(Village.objects.all())
        centre_list = list(centres.values())
        for i, v in enumerate(villages):
            centre = centre_list[i % len(centre_list)]
            RattachementVillage.objects.get_or_create(
                village=v, centre=centre,
                defaults={'date_debut': datetime.date(2010, 1, 1)}
            )

        self.stdout.write(f'   ✓ {len(centres)} centres créés')
        return centres

    # ─── Agents ───────────────────────────────────────────────────────────────

    def _creer_agents(self, centres):
        self.stdout.write('👤 Création des agents (1 superviseur + 3 agents / centre)...')

        agents = []
        mat_num = 1

        for centre in centres.values():
            for role, count in [(Agent.SUPERVISEUR_CENTRE, 1), (Agent.AGENT_GUICHET, 3)]:
                for _ in range(count):
                    nom    = random.choice(NOMS)
                    sexe   = random.choice(['M', 'F'])
                    prenom = random.choice(PRENOMS_M if sexe == 'M' else PRENOMS_F)
                    email  = f'{nom.lower()}.{prenom.lower()}{mat_num}@etatcivil.ci'
                    mat    = f'AGT-{mat_num:04d}'
                    if not Agent.objects.filter(email=email).exists():
                        a = Agent.objects.create_user(
                            email=email, password='Agent@2026CI',
                            nom=nom, prenoms=prenom, matricule=mat,
                            role=role, centre=centre,
                        )
                        agents.append(a)
                    mat_num += 1

        # Superviseur national
        if not Agent.objects.filter(email='superviseur.national@etatcivil.ci').exists():
            a = Agent.objects.create_user(
                email='superviseur.national@etatcivil.ci', password='SupNat@2026CI',
                nom='DIALLO', prenoms='Moussa', matricule='SUP-NAT-001',
                role=Agent.SUPERVISEUR_NATIONAL, centre=None,
            )
            agents.append(a)

        self.stdout.write(f'   ✓ {len(agents)} agents créés')
        return agents

    # ─── Individus ────────────────────────────────────────────────────────────

    def _creer_individus(self, centres, nb=1200):
        self.stdout.write(f'🧑 Création de {nb} individus (pyramide des âges réaliste)...')
        from individus.models import calculer_hash_biographique

        centres_list = list(centres.values())
        individus    = []
        nin_num      = 1

        # Distribution des âges : pyramide CI (jeunesse = 0-14 ans = 42 %)
        # Cohortes : 0-14, 15-30, 31-50, 51-70, 71+
        COHORTES = [
            (2011, 2025, 0.30),  # enfants (pour les naissances récentes)
            (1995, 2010, 0.28),  # jeunes adultes
            (1975, 1994, 0.22),  # adultes
            (1955, 1974, 0.13),  # seniors
            (1930, 1954, 0.07),  # âgés / décédés potentiels
        ]

        for annee_min, annee_max, proportion in COHORTES:
            n_cohorte = int(nb * proportion)
            for _ in range(n_cohorte):
                nom    = random.choice(NOMS)
                sexe   = random.choice(['M', 'F'])
                prenom = random.choice(PRENOMS_M if sexe == 'M' else PRENOMS_F)
                lieu   = random.choice(LIEUX_NAISSANCE)
                centre = random.choice(centres_list)
                annee  = random.randint(annee_min, annee_max)
                mois   = random.randint(1, 12)
                jour   = random.randint(1, 28)
                ddn    = datetime.date(annee, mois, jour)
                nin    = f'NIN-CI-{nin_num:07d}'

                h = calculer_hash_biographique(nom, prenom, ddn, lieu)
                if Individu.objects.filter(hash_biographique=h).exists() or \
                   Individu.objects.filter(nin=nin).exists():
                    nin_num += 1
                    continue

                ind = Individu.objects.create(
                    nin=nin, nom=nom, prenoms=prenom, sexe=sexe,
                    date_naissance=ddn, lieu_naissance_libelle=lieu,
                    nationalite='Ivoirienne', centre_naissance=centre,
                )
                individus.append(ind)
                nin_num += 1

        self.stdout.write(f'   ✓ {len(individus)} individus créés')
        return individus

    # ─── Actes ────────────────────────────────────────────────────────────────

    def _creer_actes(self, agents, individus, centres):
        """
        Génère des actes sur 2020-2025 avec saisonnalité et gradient urbain/rural.
        Volumes par centre proportionnels au poids défini dans CENTRES_DATA.
        """
        self.stdout.write('📄 Création des actes (2020-2025 avec saisonnalité)...')

        # Index agents par centre
        agents_gc    = {}   # AGENT_GUICHET
        superviseurs = {}   # SUPERVISEUR_CENTRE
        for a in Agent.objects.filter(role__in=[Agent.AGENT_GUICHET, Agent.SUPERVISEUR_CENTRE]):
            if a.centre:
                if a.role == Agent.AGENT_GUICHET:
                    agents_gc.setdefault(str(a.centre.id), []).append(a)
                else:
                    superviseurs.setdefault(str(a.centre.id), []).append(a)

        # Individus par cohorte
        individus_enfants  = [i for i in individus if i.date_naissance.year >= 2010]
        individus_adultes  = [i for i in individus
                              if 1975 <= i.date_naissance.year <= 2005 and not i.est_decede]
        individus_hommes   = [i for i in individus_adultes if i.sexe == 'M']
        individus_femmes   = [i for i in individus_adultes if i.sexe == 'F']
        individus_ages     = [i for i in individus if i.date_naissance.year <= 1960]

        # Poids des centres
        poids_map = {code: p for code, *_, p in CENTRES_DATA}
        total_poids = sum(poids_map.values())

        actes = []
        ANNEES = list(range(2020, 2026))

        # ── 1. NAISSANCES ──────────────────────────────────────────────────
        # ~900 actes sur 6 ans, distribués par centre et mois
        nb_naissances_total = 900
        random.shuffle(individus_enfants)
        pool_naissance = individus_enfants[:min(nb_naissances_total, len(individus_enfants))]

        # Compléter avec individus adultes si pas assez d'enfants
        if len(pool_naissance) < nb_naissances_total:
            adultes_extra = [i for i in individus if i not in pool_naissance]
            pool_naissance += adultes_extra[:nb_naissances_total - len(pool_naissance)]

        idx = 0
        for code, *_, poids in CENTRES_DATA:
            centre = Centre.objects.get(code=code)
            cid    = str(centre.id)
            agents_c = agents_gc.get(cid, [])
            sups_c   = superviseurs.get(cid, [])
            if not agents_c:
                continue

            nb_centre = max(1, int(nb_naissances_total * poids / total_poids))
            trend_factor = 1.0

            for annee in ANNEES:
                trend_factor = 1.0 + 0.05 * (annee - TREND_YEAR_BASE)
                for mois in range(1, 13):
                    if not appliquer_poids_mensuel(annee, mois, NAISSANCE_WEIGHT):
                        continue
                    n_mois = max(1, int(nb_centre / 12 * trend_factor * NAISSANCE_WEIGHT[mois-1]))
                    for _ in range(n_mois):
                        if idx >= len(pool_naissance):
                            break
                        individu = pool_naissance[idx]; idx += 1
                        date_evt = date_aleatoire(annee, mois, NAISSANCE_WEIGHT)
                        acte = Acte.objects.create(
                            nature=Acte.NAISSANCE,
                            individu=individu,
                            centre=centre,
                            date_evenement=date_evt,
                            agent=random.choice(agents_c),
                        )
                        ActeNaissance.objects.create(
                            acte=acte,
                            declarant_nom=random.choice(NOMS),
                            declarant_prenoms=random.choice(PRENOMS_M),
                            declarant_lien='Père',
                            etablissement=random.choice(HOPITAUX),
                            heure_naissance=datetime.time(random.randint(0,23), random.randint(0,59)),
                            poids_naissance=Decimal(str(round(random.uniform(2.3, 4.5), 3))),
                        )
                        # 75 % validés
                        if sups_c and random.random() < 0.75:
                            acte.valider(superviseur=random.choice(sups_c))
                        actes.append(acte)

        # ── 2. MARIAGES ────────────────────────────────────────────────────
        nb_mariages_total = 350
        random.shuffle(individus_hommes)
        random.shuffle(individus_femmes)
        paires_mariage = list(zip(
            individus_hommes[:nb_mariages_total],
            individus_femmes[:nb_mariages_total],
        ))

        idx = 0
        for code, *_, poids in CENTRES_DATA:
            centre   = Centre.objects.get(code=code)
            cid      = str(centre.id)
            agents_c = agents_gc.get(cid, [])
            sups_c   = superviseurs.get(cid, [])
            if not agents_c:
                continue

            nb_centre = max(1, int(nb_mariages_total * poids / total_poids))

            for annee in ANNEES:
                trend_factor = 1.0 + 0.04 * (annee - TREND_YEAR_BASE)
                for mois in range(1, 13):
                    if not appliquer_poids_mensuel(annee, mois, MARIAGE_WEIGHT):
                        continue
                    n_mois = max(1, int(nb_centre / 12 * trend_factor * MARIAGE_WEIGHT[mois-1]))
                    for _ in range(n_mois):
                        if idx >= len(paires_mariage):
                            break
                        epoux, epouse = paires_mariage[idx]; idx += 1
                        if epoux.est_decede or epouse.est_decede:
                            continue
                        date_evt = date_aleatoire(annee, mois, MARIAGE_WEIGHT)
                        acte = Acte.objects.create(
                            nature=Acte.MARIAGE,
                            individu=epoux,
                            centre=centre,
                            date_evenement=date_evt,
                            agent=random.choice(agents_c),
                        )
                        ActeMariage.objects.create(
                            acte=acte,
                            epoux=epoux,
                            epouse=epouse,
                            regime_matrimonial=random.choice([
                                'Communauté de biens', 'Séparation de biens', ''
                            ]),
                            officiant_nom=f'{random.choice(NOMS)} {random.choice(PRENOMS_M)}',
                            temoin1_nom=f'{random.choice(NOMS)} {random.choice(PRENOMS_M)}',
                            temoin2_nom=f'{random.choice(NOMS)} {random.choice(PRENOMS_F)}',
                        )
                        if sups_c and random.random() < 0.68:
                            acte.valider(superviseur=random.choice(sups_c))
                        actes.append(acte)

        # ── 3. DÉCÈS ───────────────────────────────────────────────────────
        nb_deces_total = 200
        random.shuffle(individus_ages)
        pool_deces = individus_ages[:nb_deces_total]

        idx = 0
        for code, *_, poids in CENTRES_DATA:
            centre   = Centre.objects.get(code=code)
            cid      = str(centre.id)
            agents_c = agents_gc.get(cid, [])
            sups_c   = superviseurs.get(cid, [])
            if not agents_c:
                continue

            nb_centre = max(1, int(nb_deces_total * poids / total_poids))

            for annee in ANNEES:
                trend_factor = 1.0 + 0.03 * (annee - TREND_YEAR_BASE)
                for mois in range(1, 13):
                    if not appliquer_poids_mensuel(annee, mois, DECES_WEIGHT):
                        continue
                    n_mois = max(1, int(nb_centre / 12 * trend_factor * DECES_WEIGHT[mois-1]))
                    for _ in range(n_mois):
                        if idx >= len(pool_deces):
                            break
                        individu = pool_deces[idx]; idx += 1
                        if individu.est_decede:
                            continue
                        date_evt = date_aleatoire(annee, mois, DECES_WEIGHT)
                        acte = Acte.objects.create(
                            nature=Acte.DECES,
                            individu=individu,
                            centre=centre,
                            date_evenement=date_evt,
                            agent=random.choice(agents_c),
                        )
                        ActeDeces.objects.create(
                            acte=acte,
                            lieu_deces=random.choice([
                                'CHU de Cocody', 'CHR de Bouaké', 'Domicile',
                                'Clinique privée', 'CHR de Daloa', 'Hôpital de Man',
                            ]),
                            cause_deces=random.choice(CAUSES_DECES),
                            declarant_nom=random.choice(NOMS),
                            declarant_prenoms=random.choice(PRENOMS_M + PRENOMS_F),
                            declarant_lien=random.choice(['Fils', 'Fille', 'Époux', 'Épouse', 'Frère']),
                        )
                        # Tous les décès sont validés → R6 verrouillage
                        if sups_c:
                            acte.valider(superviseur=random.choice(sups_c))
                        actes.append(acte)

        # ── 4. ANOMALIES / CAS SUSPECTS (pour chapitre détection fraude) ──
        self._creer_anomalies(agents_gc, superviseurs)

        self.stdout.write(f'   ✓ {Acte.objects.count()} actes créés  '
                          f'({Acte.objects.filter(nature="NAISSANCE").count()} naissances · '
                          f'{Acte.objects.filter(nature="MARIAGE").count()} mariages · '
                          f'{Acte.objects.filter(nature="DECES").count()} décès)')
        return Acte.objects.all()

    def _creer_anomalies(self, agents_gc, superviseurs):
        """
        Insère quelques patterns anormaux utilisables pour la détection de fraude :
        - Pics inhabituels sur un seul centre (burst d'actes le même jour)
        - Individus avec noms quasi-identiques (doublon potentiel)
        """
        from individus.models import calculer_hash_biographique

        centre = Centre.objects.filter(type='SOUS_PREFECTURE').first()
        if not centre:
            return
        cid = str(centre.id)
        agents_c = agents_gc.get(cid, [])
        if not agents_c:
            return

        # 15 naissances le même jour (burst suspect)
        date_suspecte = datetime.date(2023, 3, 15)
        for k in range(15):
            nom = 'KOUAME'
            prenom = f'Suspect{k:02d}'
            nin = f'NIN-CI-SUS-{k:04d}'
            h = calculer_hash_biographique(nom, prenom, date_suspecte, 'Abidjan')
            if not Individu.objects.filter(hash_biographique=h).exists() and \
               not Individu.objects.filter(nin=nin).exists():
                ind = Individu.objects.create(
                    nin=nin, nom=nom, prenoms=prenom, sexe='M',
                    date_naissance=date_suspecte,
                    lieu_naissance_libelle='Abidjan',
                    nationalite='Ivoirienne',
                    centre_naissance=centre,
                )
                acte = Acte.objects.create(
                    nature=Acte.NAISSANCE, individu=ind, centre=centre,
                    date_evenement=date_suspecte, agent=random.choice(agents_c),
                    observations='[ANOMALIE TEST] Enregistrement suspect groupé',
                )
                ActeNaissance.objects.create(
                    acte=acte, declarant_nom='KOUAME', declarant_prenoms='Jean',
                    declarant_lien='Père',
                )

    # ─── Paiements ────────────────────────────────────────────────────────────

    def _creer_paiements(self, actes, centres):
        self.stdout.write('💰 Création des demandes de copie et paiements...')

        actes_valides = list(Acte.objects.filter(statut=Acte.VALIDE))
        centres_list  = list(centres.values())

        # Tarifs selon type de copie
        TARIFS = {
            DemandeCopie.COPIE_INTEGRALE:        Decimal('1500.00'),
            DemandeCopie.EXTRAIT_AVEC_FILIATION: Decimal('1000.00'),
            DemandeCopie.EXTRAIT_SANS_FILIATION: Decimal('500.00'),
            DemandeCopie.BULLETIN:               Decimal('500.00'),
        }

        # Adoption mobile money : gradient urbain > rural
        # Abidjan : 60 % mobile, rural : 25 %
        URBAIN_CODES = {'CTR-CO1', 'CTR-PL1', 'CTR-YO1', 'CTR-AB1', 'CTR-AC1', 'CTR-PA1'}

        nb = 0
        sample_size = min(800, len(actes_valides))
        for acte in random.sample(actes_valides, sample_size):
            centre = random.choice(centres_list)
            type_c = random.choice([
                DemandeCopie.COPIE_INTEGRALE,
                DemandeCopie.EXTRAIT_AVEC_FILIATION,
                DemandeCopie.EXTRAIT_SANS_FILIATION,
                DemandeCopie.BULLETIN,
            ])
            canal = random.choices(
                [DemandeCopie.GUICHET, DemandeCopie.EN_LIGNE],
                weights=[0.65, 0.35]
            )[0]

            demande = DemandeCopie.objects.create(
                acte=acte, centre=centre,
                demandeur_nom=f'{random.choice(NOMS)} {random.choice(PRENOMS_M + PRENOMS_F)}',
                demandeur_cin=f'CI{random.randint(1000000, 9999999)}',
                demandeur_lien=random.choice(['Titulaire', 'Père', 'Mère', 'Conjoint', 'Fils', 'Fille']),
                type_copie=type_c,
                canal=canal,
            )

            # 85 % des demandes sont payées
            if random.random() < 0.85:
                # Choisir le moyen selon la zone
                if acte.centre.code in URBAIN_CODES:
                    moyen = random.choices(
                        [Paiement.ESPECES, Paiement.MTN_MONEY, Paiement.ORANGE_MONEY, Paiement.WAVE],
                        weights=[0.40, 0.25, 0.20, 0.15]
                    )[0]
                else:
                    moyen = random.choices(
                        [Paiement.ESPECES, Paiement.MTN_MONEY, Paiement.ORANGE_MONEY, Paiement.WAVE],
                        weights=[0.75, 0.12, 0.08, 0.05]
                    )[0]

                Paiement.objects.create(
                    demande=demande,
                    montant=TARIFS[type_c],
                    moyen=moyen,
                    statut=Paiement.CONFIRME,
                    date_paiement=timezone.now(),
                    recu_numero=f'REC-{random.randint(100000, 9999999)}',
                )
                demande.statut = DemandeCopie.PAYEE
                demande.save(update_fields=['statut'])
            nb += 1

        self.stdout.write(f'   ✓ {nb} demandes · {Paiement.objects.filter(statut="CONFIRME").count()} paiements confirmés')

    # ─── Mentions marginales ──────────────────────────────────────────────────

    def _creer_mentions(self, actes, agents):
        self.stdout.write('📝 Création des mentions marginales...')

        actes_naissance = list(Acte.objects.filter(nature=Acte.NAISSANCE, statut=Acte.VALIDE))
        actes_mariage   = list(Acte.objects.filter(nature=Acte.MARIAGE,   statut=Acte.VALIDE))
        agents_list     = list(Agent.objects.filter(role=Agent.AGENT_GUICHET))
        if not agents_list:
            return

        nb = 0
        # Mentions de mariage sur actes de naissance (R5-like)
        for acte_m in random.sample(actes_mariage, min(80, len(actes_mariage))):
            actes_n = [a for a in actes_naissance if a.individu == acte_m.individu]
            if actes_n:
                MentionMarginale.objects.create(
                    acte=actes_n[0],
                    type_mention=MentionMarginale.MARIAGE,
                    acte_source_ref=acte_m.numero_national,
                    centre_source=acte_m.centre,
                    date_mention=acte_m.date_evenement,
                    contenu=f'Mariage célébré le {acte_m.date_evenement} à {acte_m.centre.nom}',
                    agent=random.choice(agents_list),
                )
                nb += 1

        # Mentions de décès sur actes de naissance
        actes_deces = list(Acte.objects.filter(nature=Acte.DECES, statut=Acte.VALIDE))
        for acte_d in random.sample(actes_deces, min(50, len(actes_deces))):
            actes_n = [a for a in actes_naissance if a.individu == acte_d.individu]
            if actes_n:
                MentionMarginale.objects.create(
                    acte=actes_n[0],
                    type_mention=MentionMarginale.DECES,
                    acte_source_ref=acte_d.numero_national,
                    centre_source=acte_d.centre,
                    date_mention=acte_d.date_evenement,
                    contenu=f'Décès survenu le {acte_d.date_evenement} à {acte_d.centre.nom}',
                    agent=random.choice(agents_list),
                )
                nb += 1

        self.stdout.write(f'   ✓ {nb} mentions marginales créées')

    # ─── Notifications ────────────────────────────────────────────────────────

    def _creer_notifications(self, actes, centres):
        self.stdout.write('🔔 Création des notifications inter-centres...')

        centres_list   = list(centres.values())
        actes_cibles   = list(Acte.objects.filter(
            statut=Acte.VALIDE,
            nature__in=[Acte.MARIAGE, Acte.DECES]
        ))
        nb = 0

        for acte in random.sample(actes_cibles, min(200, len(actes_cibles))):
            emetteur     = acte.centre
            destinataire = random.choice([c for c in centres_list if c.id != emetteur.id])
            statut       = random.choices(
                [NotificationInterCentre.EN_ATTENTE,
                 NotificationInterCentre.ENVOYEE,
                 NotificationInterCentre.ACQUITTEE],
                weights=[0.30, 0.40, 0.30]
            )[0]

            notif = NotificationInterCentre.objects.create(
                acte_declencheur=acte,
                centre_emetteur=emetteur,
                centre_destinataire=destinataire,
                type_evenement=f'{acte.nature}_INTER_CENTRE',
                statut=statut,
                payload={
                    'acte_id':      str(acte.id),
                    'individu_nin': acte.individu.nin,
                    'nature':       acte.nature,
                    'date':         str(acte.date_evenement),
                    'centre_emit':  emetteur.code,
                },
            )
            if statut == NotificationInterCentre.ACQUITTEE:
                notif.date_acquittement = timezone.now()
                notif.save(update_fields=['date_acquittement'])
            nb += 1

        self.stdout.write(f'   ✓ {nb} notifications inter-centres créées')

    # ─── Résumé ───────────────────────────────────────────────────────────────

    def _afficher_resume(self):
        self.stdout.write('\n' + '═' * 60)
        self.stdout.write(self.style.SUCCESS('📊  RÉSUMÉ DES DONNÉES — MÉMOIRE SID M2'))
        self.stdout.write('═' * 60)
        self.stdout.write(f'  Régions          : {Region.objects.count()}')
        self.stdout.write(f'  Départements     : {Departement.objects.count()}')
        self.stdout.write(f'  Localités        : {Localite.objects.count()}')
        self.stdout.write(f'  Villages         : {Village.objects.count()}')
        self.stdout.write(f'  Centres          : {Centre.objects.count()} '
                          f'({Centre.objects.filter(type="SOUS_PREFECTURE").count()} SP · '
                          f'{Centre.objects.filter(type="MAIRIE").count()} mairies)')
        self.stdout.write(f'  Agents           : {Agent.objects.filter(is_superuser=False).count()}')
        self.stdout.write(f'  Individus        : {Individu.objects.count()}')
        self.stdout.write(f'  — dont décédés   : {Individu.objects.filter(est_decede=True).count()}')
        self.stdout.write(f'  Actes TOTAL      : {Acte.objects.count()}')
        self.stdout.write(f'  — Naissances     : {Acte.objects.filter(nature="NAISSANCE").count()}')
        self.stdout.write(f'  — Mariages       : {Acte.objects.filter(nature="MARIAGE").count()}')
        self.stdout.write(f'  — Décès          : {Acte.objects.filter(nature="DECES").count()}')
        self.stdout.write(f'  — Validés        : {Acte.objects.filter(statut="VALIDE").count()}')
        self.stdout.write(f'  — Brouillons     : {Acte.objects.filter(statut="BROUILLON").count()}')
        self.stdout.write(f'  Mentions marg.   : {MentionMarginale.objects.count()}')
        self.stdout.write(f'  Demandes copie   : {DemandeCopie.objects.count()}')
        self.stdout.write(f'  Paiements conf.  : {Paiement.objects.filter(statut="CONFIRME").count()}')
        self.stdout.write(f'  Notifications    : {NotificationInterCentre.objects.count()}')
        self.stdout.write(f'  — En attente     : {NotificationInterCentre.objects.filter(statut="EN_ATTENTE").count()}')
        self.stdout.write(f'  — Acquittées     : {NotificationInterCentre.objects.filter(statut="ACQUITTEE").count()}')

        from paiements.models import Paiement as P
        from django.db.models import Sum
        recettes = P.objects.filter(statut='CONFIRME').aggregate(t=Sum('montant'))['t'] or 0
        self.stdout.write(f'  Recettes totales : {int(recettes):,} FCFA')
        self.stdout.write('═' * 60)
        self.stdout.write('\n🔑 Agents         : Agent@2026CI')
        self.stdout.write('🔑 Sup. national  : superviseur.national@etatcivil.ci / SupNat@2026CI')
        self.stdout.write('🔑 Admin système  : admin@etatcivil.ci / Admin@2026CI\n')
