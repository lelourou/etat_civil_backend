"""
Commande de génération de données de démonstration.
Usage : python manage.py seed_data
"""
import random
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone

from territoire.models  import Region, Departement, Localite, Village
from centres.models     import Centre, RattachementVillage
from authentification.models import Agent
from individus.models   import Individu, Filiation
from actes.models       import Acte, ActeNaissance, ActeMariage, ActeDeces, MentionMarginale
from paiements.models   import DemandeCopie, Paiement
from notifications.models import NotificationInterCentre


# ── Données géographiques réelles (Côte d'Ivoire) ─────────────────────────────

REGIONS = [
    ('RG-AB', 'Abidjan'),
    ('RG-LA', 'Lagunes'),
    ('RG-GD', 'Gôh-Djiboua'),
    ('RG-SS', 'Sassandra-Marahoué'),
    ('RG-VB', 'Vallée du Bandama'),
    ('RG-ZZ', 'Zanzan'),
]

DEPARTEMENTS = [
    ('DP-CO', 'Cocody',       'RG-AB'),
    ('DP-PL', 'Plateau',      'RG-AB'),
    ('DP-YO', 'Yopougon',     'RG-AB'),
    ('DP-AB', 'Abobo',        'RG-AB'),
    ('DP-AC', 'Adjamé',       'RG-AB'),
    ('DP-JA', 'Jacqueville',  'RG-LA'),
    ('DP-DA', 'Dabou',        'RG-LA'),
    ('DP-DI', 'Divo',         'RG-GD'),
    ('DP-DG', 'Daloa',        'RG-SS'),
    ('DP-BK', 'Bouaké',       'RG-VB'),
    ('DP-BG', 'Bondoukou',    'RG-ZZ'),
]

LOCALITES = [
    ('LC-CO1', 'Cocody-Riviera',   'DP-CO'),
    ('LC-CO2', 'Cocody-2 Plateaux','DP-CO'),
    ('LC-PL1', 'Plateau-Centre',   'DP-PL'),
    ('LC-YO1', 'Yopougon-Selmer',  'DP-YO'),
    ('LC-YO2', 'Yopougon-Maroc',   'DP-YO'),
    ('LC-AB1', 'Abobo-Centre',     'DP-AB'),
    ('LC-AB2', 'Abobo-Gare',       'DP-AB'),
    ('LC-AC1', 'Adjamé-Liberté',   'DP-AC'),
    ('LC-JA1', 'Jacqueville-Centre','DP-JA'),
    ('LC-DA1', 'Dabou-Centre',     'DP-DA'),
    ('LC-DI1', 'Divo-Centre',      'DP-DI'),
    ('LC-DG1', 'Daloa-Centre',     'DP-DG'),
    ('LC-BK1', 'Bouaké-Nord',      'DP-BK'),
    ('LC-BG1', 'Bondoukou-Centre', 'DP-BG'),
]

VILLAGES = [
    ('VL-001', 'Riviera 2',        'LC-CO1'),
    ('VL-002', 'Riviera Palmeraie','LC-CO1'),
    ('VL-003', 'Cocody-Danga',     'LC-CO2'),
    ('VL-004', 'Plateau-Akwaba',   'LC-PL1'),
    ('VL-005', 'Selmer Village',   'LC-YO1'),
    ('VL-006', 'Maroc-Centre',     'LC-YO2'),
    ('VL-007', 'Abobo-Baoulé',     'LC-AB1'),
    ('VL-008', 'Gare-Nord',        'LC-AB2'),
    ('VL-009', 'Liberté-3',        'LC-AC1'),
    ('VL-010', 'Jacqueville-Plage','LC-JA1'),
    ('VL-011', 'Dabou-Lagune',     'LC-DA1'),
    ('VL-012', 'Divo-Marché',      'LC-DI1'),
    ('VL-013', 'Daloa-Tazibouo',   'LC-DG1'),
    ('VL-014', 'Bouaké-Bromakoté', 'LC-BK1'),
    ('VL-015', 'Bondoukou-Zanzan', 'LC-BG1'),
]

CENTRES_DATA = [
    ('CTR-CO1', 'Sous-Préfecture de Cocody',         'SOUS_PREFECTURE', 'LC-CO1'),
    ('CTR-PL1', 'Mairie du Plateau',                 'MAIRIE',          'LC-PL1'),
    ('CTR-YO1', 'Sous-Préfecture de Yopougon',       'SOUS_PREFECTURE', 'LC-YO1'),
    ('CTR-AB1', 'Mairie d\'Abobo',                   'MAIRIE',          'LC-AB1'),
    ('CTR-AC1', 'Sous-Préfecture d\'Adjamé',         'SOUS_PREFECTURE', 'LC-AC1'),
    ('CTR-DA1', 'Mairie de Dabou',                   'MAIRIE',          'LC-DA1'),
    ('CTR-DI1', 'Sous-Préfecture de Divo',           'SOUS_PREFECTURE', 'LC-DI1'),
    ('CTR-DG1', 'Mairie de Daloa',                   'MAIRIE',          'LC-DG1'),
    ('CTR-BK1', 'Sous-Préfecture de Bouaké',         'SOUS_PREFECTURE', 'LC-BK1'),
    ('CTR-BG1', 'Mairie de Bondoukou',               'MAIRIE',          'LC-BG1'),
]

# ── Noms ivoiriens typiques ────────────────────────────────────────────────────

NOMS = [
    'KOUAME', 'KONAN', 'KOFFI', 'YAO', 'BROU',
    'TRAORE', 'COULIBALY', 'DIALLO', 'BAMBA', 'TOURE',
    'OUATTARA', 'KONE', 'CAMARA', 'DIOMANDE', 'SANGARE',
    'ASSI', 'AHOUA', 'AHORE', 'GNAGNE', 'GBAGBO',
    'BLE', 'GUEHI', 'DAHO', 'TAPE', 'PEHE',
]

PRENOMS_M = [
    'Jean', 'Paul', 'Pierre', 'Jacques', 'Henri',
    'Kouadio', 'Kofi', 'Koffi', 'Yao', 'Kouassi',
    'Amara', 'Mamadou', 'Ibrahim', 'Moussa', 'Issouf',
    'Adama', 'Seydou', 'Aboubacar', 'Drissa', 'Souleymane',
    'Maxime', 'Franck', 'Didier', 'Serge', 'Eric',
]

PRENOMS_F = [
    'Marie', 'Aïcha', 'Fatou', 'Aminata', 'Mariam',
    'Adjoua', 'Akissi', 'Affoue', 'Amenan', 'Assata',
    'Fatoumata', 'Hawa', 'Salimata', 'Rokia', 'Djeneba',
    'Aya', 'Bintou', 'Chantal', 'Estelle', 'Nadège',
]

LIEUX_NAISSANCE = [
    'Abidjan', 'Bouaké', 'Daloa', 'Korhogo', 'San-Pédro',
    'Yamoussoukro', 'Divo', 'Man', 'Gagnoa', 'Abengourou',
    'Bondoukou', 'Dabou', 'Jacqueville', 'Agboville', 'Adzopé',
]


class Command(BaseCommand):
    help = 'Génère des données de démonstration réalistes pour la Côte d\'Ivoire'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Supprimer toutes les données existantes avant de générer')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Génération des données État Civil CI ===\n'))

        regions    = self._creer_territoire()
        centres    = self._creer_centres()
        agents     = self._creer_agents(centres)
        individus  = self._creer_individus(centres)
        actes      = self._creer_actes(agents, individus, centres)
        self._creer_paiements(actes, centres)
        self._creer_notifications(actes, centres)

        self.stdout.write(self.style.SUCCESS('\n✅ Données générées avec succès !\n'))
        self._afficher_resume(centres, agents, individus, actes)

    # ── Clear ──────────────────────────────────────────────────────────────────

    def _clear_data(self):
        NotificationInterCentre.objects.all().delete()
        Paiement.objects.all().delete()
        DemandeCopie.objects.all().delete()
        MentionMarginale.objects.all().delete()
        ActeNaissance.objects.all().delete()
        ActeMariage.objects.all().delete()
        ActeDeces.objects.all().delete()
        Acte.objects.all().delete()
        Filiation.objects.all().delete()
        Individu.objects.all().delete()
        Agent.objects.filter(is_superuser=False).delete()
        RattachementVillage.objects.all().delete()
        Centre.objects.all().delete()
        Village.objects.all().delete()
        Localite.objects.all().delete()
        Departement.objects.all().delete()
        Region.objects.all().delete()

    # ── Territoire ─────────────────────────────────────────────────────────────

    def _creer_territoire(self):
        self.stdout.write('📍 Création du territoire...')

        regions = {}
        for code, nom in REGIONS:
            r, _ = Region.objects.get_or_create(code=code, defaults={'nom': nom})
            regions[code] = r

        departements = {}
        for code, nom, reg_code in DEPARTEMENTS:
            d, _ = Departement.objects.get_or_create(
                code=code, defaults={'nom': nom, 'region': regions[reg_code]}
            )
            departements[code] = d

        localites = {}
        for code, nom, dept_code in LOCALITES:
            l, _ = Localite.objects.get_or_create(
                code=code, defaults={'nom': nom, 'departement': departements[dept_code]}
            )
            localites[code] = l

        villages = {}
        for code, nom, loc_code in VILLAGES:
            v, _ = Village.objects.get_or_create(
                code=code, defaults={'nom': nom, 'localite': localites[loc_code]}
            )
            villages[code] = v

        self.stdout.write(f'   {len(regions)} régions, {len(departements)} départements, '
                          f'{len(localites)} localités, {len(villages)} villages')
        return regions

    # ── Centres ────────────────────────────────────────────────────────────────

    def _creer_centres(self):
        self.stdout.write('🏛️  Création des centres...')

        localites = {l.code: l for l in Localite.objects.all()}
        centres = {}

        for code, nom, type_centre, loc_code in CENTRES_DATA:
            c, _ = Centre.objects.get_or_create(
                code=code,
                defaults={
                    'nom': nom,
                    'type': type_centre,
                    'localite': localites[loc_code],
                    'date_creation': datetime.date(2010, 1, 1),
                    'telephone': f'+225 27 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99):02d}',
                    'email': f'{code.lower().replace("-",".")}@etatcivil.ci',
                }
            )
            centres[code] = c

        # Rattacher les villages aux centres proches
        villages = list(Village.objects.all())
        for i, village in enumerate(villages):
            centre = list(centres.values())[i % len(centres)]
            RattachementVillage.objects.get_or_create(
                village=village, centre=centre,
                defaults={'date_debut': datetime.date(2010, 1, 1)}
            )

        self.stdout.write(f'   {len(centres)} centres créés')
        return centres

    # ── Agents ─────────────────────────────────────────────────────────────────

    def _creer_agents(self, centres):
        self.stdout.write('👤 Création des agents...')

        agents = []
        centres_list = list(centres.values())

        roles_config = [
            (Agent.SUPERVISEUR_CENTRE,   1),   # 1 superviseur par centre
            (Agent.AGENT_GUICHET,        3),   # 3 agents par centre
        ]

        matricule_num = 1
        for centre in centres_list:
            for role, count in roles_config:
                for _ in range(count):
                    nom    = random.choice(NOMS)
                    sexe   = random.choice(['M', 'F'])
                    prenom = random.choice(PRENOMS_M if sexe == 'M' else PRENOMS_F)
                    email  = f'{nom.lower()}.{prenom.lower()}{matricule_num}@etatcivil.ci'
                    matricule = f'AGT-{matricule_num:04d}'

                    if not Agent.objects.filter(email=email).exists():
                        agent = Agent.objects.create_user(
                            email=email,
                            password='Agent@2026CI',
                            nom=nom,
                            prenoms=prenom,
                            matricule=matricule,
                            role=role,
                            centre=centre,
                        )
                        agents.append(agent)
                    matricule_num += 1

        # 1 superviseur national
        if not Agent.objects.filter(email='superviseur.national@etatcivil.ci').exists():
            sup_nat = Agent.objects.create_user(
                email='superviseur.national@etatcivil.ci',
                password='SupNat@2026CI',
                nom='DIALLO',
                prenoms='Moussa',
                matricule='SUP-NAT-001',
                role=Agent.SUPERVISEUR_NATIONAL,
                centre=None,
            )
            agents.append(sup_nat)

        self.stdout.write(f'   {len(agents)} agents créés')
        return agents

    # ── Individus ──────────────────────────────────────────────────────────────

    def _creer_individus(self, centres):
        self.stdout.write('🧑 Création des individus...')

        centres_list = list(centres.values())
        individus = []
        nin_num = 1

        for i in range(120):
            nom    = random.choice(NOMS)
            sexe   = random.choice(['M', 'F'])
            prenom = random.choice(PRENOMS_M if sexe == 'M' else PRENOMS_F)
            lieu   = random.choice(LIEUX_NAISSANCE)
            centre = random.choice(centres_list)
            annee  = random.randint(1950, 2010)
            mois   = random.randint(1, 12)
            jour   = random.randint(1, 28)
            ddn    = datetime.date(annee, mois, jour)
            nin    = f'NIN-CI-{nin_num:06d}'

            # Éviter les doublons de hash
            from individus.models import calculer_hash_biographique
            h = calculer_hash_biographique(nom, prenom, ddn, lieu)
            if Individu.objects.filter(hash_biographique=h).exists():
                nin_num += 1
                continue

            if not Individu.objects.filter(nin=nin).exists():
                ind = Individu.objects.create(
                    nin=nin,
                    nom=nom,
                    prenoms=prenom,
                    sexe=sexe,
                    date_naissance=ddn,
                    lieu_naissance_libelle=lieu,
                    nationalite='Ivoirienne',
                    centre_naissance=centre,
                )
                individus.append(ind)
            nin_num += 1

        self.stdout.write(f'   {len(individus)} individus créés')
        return individus

    # ── Actes ──────────────────────────────────────────────────────────────────

    def _creer_actes(self, agents, individus, centres):
        self.stdout.write('📄 Création des actes...')

        actes = []
        agents_by_centre = {}
        superviseurs_by_centre = {}

        for agent in agents:
            if agent.centre:
                agents_by_centre.setdefault(agent.centre.id, [])
                superviseurs_by_centre.setdefault(agent.centre.id, [])
                if agent.role == Agent.AGENT_GUICHET:
                    agents_by_centre[agent.centre.id].append(agent)
                elif agent.role == Agent.SUPERVISEUR_CENTRE:
                    superviseurs_by_centre[agent.centre.id].append(agent)

        centres_list = list(centres.values())

        # 1. Actes de NAISSANCE (60 actes)
        for individu in individus[:60]:
            centre = random.choice(centres_list)
            agents_c = agents_by_centre.get(centre.id, [])
            if not agents_c:
                continue
            agent = random.choice(agents_c)
            date_evt = individu.date_naissance

            acte = Acte.objects.create(
                nature=Acte.NAISSANCE,
                individu=individu,
                centre=centre,
                date_evenement=date_evt,
                agent=agent,
                observations='Acte enregistré au guichet.',
            )

            ActeNaissance.objects.create(
                acte=acte,
                declarant_nom=random.choice(NOMS),
                declarant_prenoms=random.choice(PRENOMS_M),
                declarant_lien='Père',
                etablissement=random.choice(['CHU de Cocody', 'Clinique Sainte Marie',
                                             'Maternité centrale', 'CHR de Bouaké', '']),
                heure_naissance=datetime.time(random.randint(0,23), random.randint(0,59)),
            )

            # 70% des actes sont validés
            sups = superviseurs_by_centre.get(centre.id, [])
            if sups and random.random() < 0.70:
                sup = random.choice(sups)
                acte.valider(superviseur=sup)

            actes.append(acte)

        # 2. Actes de MARIAGE (20 actes)
        individus_adultes = [i for i in individus if i.date_naissance.year <= 1998 and not i.est_decede]
        hommes  = [i for i in individus_adultes if i.sexe == 'M']
        femmes  = [i for i in individus_adultes if i.sexe == 'F']
        nb_mariages = min(20, len(hommes), len(femmes))

        random.shuffle(hommes)
        random.shuffle(femmes)

        for i in range(nb_mariages):
            epoux  = hommes[i]
            epouse = femmes[i]
            centre = random.choice(centres_list)
            agents_c = agents_by_centre.get(centre.id, [])
            if not agents_c:
                continue
            agent = random.choice(agents_c)
            annee = random.randint(2015, 2025)
            date_evt = datetime.date(annee, random.randint(1,12), random.randint(1,28))

            acte = Acte.objects.create(
                nature=Acte.MARIAGE,
                individu=epoux,
                centre=centre,
                date_evenement=date_evt,
                agent=agent,
            )

            ActeMariage.objects.create(
                acte=acte,
                epoux=epoux,
                epouse=epouse,
                regime_matrimonial=random.choice(['Communauté de biens', 'Séparation de biens', '']),
                officiant_nom=f'{random.choice(NOMS)} {random.choice(PRENOMS_M)}',
            )

            sups = superviseurs_by_centre.get(centre.id, [])
            if sups and random.random() < 0.60:
                acte.valider(superviseur=random.choice(sups))

            actes.append(acte)

        # 3. Actes de DÉCÈS (10 actes)
        individus_a_deces = [i for i in individus
                             if i.date_naissance.year <= 1960 and not i.est_decede][:10]

        for individu in individus_a_deces:
            centre = random.choice(centres_list)
            agents_c = agents_by_centre.get(centre.id, [])
            if not agents_c:
                continue
            agent = random.choice(agents_c)
            annee = random.randint(2020, 2025)
            date_evt = datetime.date(annee, random.randint(1,12), random.randint(1,28))

            acte = Acte.objects.create(
                nature=Acte.DECES,
                individu=individu,
                centre=centre,
                date_evenement=date_evt,
                agent=agent,
            )

            ActeDeces.objects.create(
                acte=acte,
                lieu_deces=random.choice(['CHU de Cocody', 'CHR de Bouaké', 'Domicile', 'Clinique']),
                cause_deces=random.choice(['Maladie', 'Accident', 'Vieillesse', '']),
                declarant_nom=random.choice(NOMS),
                declarant_prenoms=random.choice(PRENOMS_M),
                declarant_lien='Fils',
            )

            # Valider le décès → déclenche R6 (verrouillage)
            sups = superviseurs_by_centre.get(centre.id, [])
            if sups:
                acte.valider(superviseur=random.choice(sups))

            actes.append(acte)

        self.stdout.write(f'   {len(actes)} actes créés')
        return actes

    # ── Paiements ──────────────────────────────────────────────────────────────

    def _creer_paiements(self, actes, centres):
        self.stdout.write('💰 Création des demandes de copie et paiements...')

        actes_valides = [a for a in actes if a.statut == Acte.VALIDE]
        centres_list  = list(centres.values())
        nb = 0

        for acte in random.sample(actes_valides, min(30, len(actes_valides))):
            centre = random.choice(centres_list)
            demande = DemandeCopie.objects.create(
                acte=acte,
                centre=centre,
                demandeur_nom=f'{random.choice(NOMS)} {random.choice(PRENOMS_M + PRENOMS_F)}',
                demandeur_cin=f'CI{random.randint(1000000, 9999999)}',
                demandeur_lien=random.choice(['Titulaire', 'Père', 'Mère', 'Conjoint', 'Fils', 'Fille']),
                type_copie=random.choice([
                    DemandeCopie.COPIE_INTEGRALE,
                    DemandeCopie.EXTRAIT_AVEC_FILIATION,
                    DemandeCopie.EXTRAIT_SANS_FILIATION,
                    DemandeCopie.BULLETIN,
                ]),
                canal=random.choice([DemandeCopie.GUICHET, DemandeCopie.EN_LIGNE]),
            )

            # 80% des demandes sont payées
            if random.random() < 0.80:
                moyen = random.choice([
                    Paiement.ESPECES, Paiement.MTN_MONEY,
                    Paiement.ORANGE_MONEY, Paiement.WAVE,
                ])
                Paiement.objects.create(
                    demande=demande,
                    montant=500.00,
                    moyen=moyen,
                    statut=Paiement.CONFIRME,
                    date_paiement=timezone.now(),
                    recu_numero=f'REC-{random.randint(100000, 999999)}',
                )
                demande.statut = DemandeCopie.PAYEE
                demande.save(update_fields=['statut'])

            nb += 1

        self.stdout.write(f'   {nb} demandes de copie créées')

    # ── Notifications ──────────────────────────────────────────────────────────

    def _creer_notifications(self, actes, centres):
        self.stdout.write('🔔 Création des notifications inter-centres...')

        centres_list = list(centres.values())
        actes_valides = [a for a in actes if a.statut == Acte.VALIDE and
                         a.nature in [Acte.MARIAGE, Acte.DECES]]
        nb = 0

        for acte in actes_valides[:15]:
            emetteur     = acte.centre
            destinataires = [c for c in centres_list if c.id != emetteur.id]
            if not destinataires:
                continue
            destinataire = random.choice(destinataires)

            statut = random.choice([
                NotificationInterCentre.ENVOYEE,
                NotificationInterCentre.ACQUITTEE,
                NotificationInterCentre.EN_ATTENTE,
            ])

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
                },
            )

            if statut == NotificationInterCentre.ACQUITTEE:
                notif.date_acquittement = timezone.now()
                notif.save(update_fields=['date_acquittement'])

            nb += 1

        self.stdout.write(f'   {nb} notifications créées')

    # ── Résumé ─────────────────────────────────────────────────────────────────

    def _afficher_resume(self, centres, agents, individus, actes):
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ DES DONNÉES GÉNÉRÉES'))
        self.stdout.write('─' * 50)
        self.stdout.write(f'  Régions         : {Region.objects.count()}')
        self.stdout.write(f'  Départements    : {Departement.objects.count()}')
        self.stdout.write(f'  Localités       : {Localite.objects.count()}')
        self.stdout.write(f'  Villages        : {Village.objects.count()}')
        self.stdout.write(f'  Centres         : {Centre.objects.count()}')
        self.stdout.write(f'  Agents          : {Agent.objects.filter(is_superuser=False).count()}')
        self.stdout.write(f'  Individus       : {Individu.objects.count()}')
        self.stdout.write(f'  Actes naissance : {Acte.objects.filter(nature=Acte.NAISSANCE).count()}')
        self.stdout.write(f'  Actes mariage   : {Acte.objects.filter(nature=Acte.MARIAGE).count()}')
        self.stdout.write(f'  Actes décès     : {Acte.objects.filter(nature=Acte.DECES).count()}')
        self.stdout.write(f'  Actes validés   : {Acte.objects.filter(statut=Acte.VALIDE).count()}')
        self.stdout.write(f'  Demandes copie  : {DemandeCopie.objects.count()}')
        self.stdout.write(f'  Paiements       : {Paiement.objects.count()}')
        self.stdout.write(f'  Notifications   : {NotificationInterCentre.objects.count()}')
        self.stdout.write('─' * 50)
        self.stdout.write('\n🔑 Accès agents (mot de passe : Agent@2026CI)')
        self.stdout.write('🔑 Superviseur national : superviseur.national@etatcivil.ci / SupNat@2026CI')
        self.stdout.write('🔑 Admin système : admin@etatcivil.ci / Admin@2026CI\n')
