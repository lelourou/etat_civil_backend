"""
Commande : python manage.py seed_demo
Peuple la base avec des données réalistes pour la présentation.
Idempotente : ne crée pas de doublons si déjà exécutée.
"""
import random
import uuid
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

Agent = get_user_model()

# ─── Données de référence ────────────────────────────────────────────────────

REGIONS = [
    ('RG-AB', 'Abidjan'),
    ('RG-BK', 'Gbêkê'),
    ('RG-DL', 'Haut-Sassandra'),
    ('RG-YM', 'Yamoussoukro'),
]

DEPARTEMENTS = [
    ('DP-PL', 'Plateau', 'RG-AB'),
    ('DP-AB', 'Abobo', 'RG-AB'),
    ('DP-YO', 'Yopougon', 'RG-AB'),
    ('DP-BK', 'Bouaké', 'RG-BK'),
    ('DP-DL', 'Daloa', 'RG-DL'),
    ('DP-YM', 'Yamoussoukro', 'RG-YM'),
]

LOCALITES = [
    ('LC-PL', 'Plateau', 'DP-PL'),
    ('LC-AB', 'Abobo', 'DP-AB'),
    ('LC-YO', 'Yopougon', 'DP-YO'),
    ('LC-BK', 'Bouaké', 'DP-BK'),
    ('LC-DL', 'Daloa', 'DP-DL'),
    ('LC-YM', 'Yamoussoukro', 'DP-YM'),
]

CENTRES = [
    ('CTR-PL1', 'Mairie du Plateau',          'MAIRIE',          'LC-PL'),
    ('CTR-AB1', "Mairie d'Abobo",              'MAIRIE',          'LC-AB'),
    ('CTR-YO1', 'Sous-Préfecture de Yopougon', 'SOUS_PREFECTURE', 'LC-YO'),
    ('CTR-BK1', 'Sous-Préfecture de Bouaké',   'SOUS_PREFECTURE', 'LC-BK'),
    ('CTR-DG1', 'Sous-Préfecture de Daloa',    'SOUS_PREFECTURE', 'LC-DL'),
    ('CTR-YM1', 'Mairie de Yamoussoukro',      'MAIRIE',          'LC-YM'),
]

VILLAGES_DATA = [
    ('VL-PL1', 'Quartier Financier',     'LC-PL'),
    ('VL-PL2', 'Zone 4',                 'LC-PL'),
    ('VL-AB1', 'Abobo-Baoulé',           'LC-AB'),
    ('VL-AB2', 'Abobo-Gare',             'LC-AB'),
    ('VL-YO1', 'Yopougon-Attié',         'LC-YO'),
    ('VL-YO2', 'Yopougon-Selmer',        'LC-YO'),
    ('VL-BK1', 'Bouaké-Centre',          'LC-BK'),
    ('VL-BK2', 'Koko',                   'LC-BK'),
    ('VL-DL1', 'Daloa-Centre',           'LC-DL'),
    ('VL-DL2', 'Lobia',                  'LC-DL'),
    ('VL-YM1', 'Quartier Millionnaire',  'LC-YM'),
    ('VL-YM2', 'N\'Zué-Konan',           'LC-YM'),
]

# Village rattaché à chaque centre
RATTACHEMENTS = {
    'CTR-PL1': ['VL-PL1', 'VL-PL2'],
    'CTR-AB1': ['VL-AB1', 'VL-AB2'],
    'CTR-YO1': ['VL-YO1', 'VL-YO2'],
    'CTR-BK1': ['VL-BK1', 'VL-BK2'],
    'CTR-DG1': ['VL-DL1', 'VL-DL2'],
    'CTR-YM1': ['VL-YM1', 'VL-YM2'],
}

AGENTS = [
    ('agent.abidjan@etatcivil.ci', 'Abidjan@2024', 'KOUAME',  'Jean-Baptiste', 'AGT-PL-001', 'CTR-PL1'),
    ('agent.bouake@etatcivil.ci',  'Bouake@2024',  'BAMBA',   'Aminata',       'AGT-BK-001', 'CTR-BK1'),
    ('agent.daloa@etatcivil.ci',   'Daloa@2024',   'GOBA',    'Emmanuel',      'AGT-DG-001', 'CTR-DG1'),
    ('agent.abobo@etatcivil.ci',   'Abobo@2024',   'YAPI',    'Christelle',    'AGT-AB-001', 'CTR-AB1'),
    ('agent.yopougon@etatcivil.ci','Yopougon@2024','TRAORE',  'Moussa',        'AGT-YO-001', 'CTR-YO1'),
    ('agent.yamousso@etatcivil.ci','Yamousso@2024','KONE',    'Siaka',         'AGT-YM-001', 'CTR-YM1'),
]

NOMS_M  = ['KOUASSI','KONAN','BAMBA','TRAORE','KONE','OUATTARA','DIALLO','COULIBALY',
           'YAPI','GOBA','AKRE','SEKA','TAPE','DJET','GNAGNE']
NOMS_F  = ['KOUAME','ASSI','GBAGBO','TOURE','FOFANA','AHOUA','YEBOUE','BLE',
           'SERI','GNEBA','LAGO','KOUA','AKA','YAO','N\'GUESSAN']
PRENOMS_M = ['Jean-Baptiste','Kofi','Moussa','Ibrahim','Siaka','Emmanuel','Wilfried',
             'Narcisse','Brice','Franck','Rodrigue','Serge','Patrick','Ghislain','Romuald']
PRENOMS_F = ['Aminata','Fatou','Christelle','Adjoua','Yolande','Sylvie','Marie-Claire',
             'Bintou','Rosine','Mariam','Cynthia','Estelle','Pauline','Aissatou','Evelyne']

MOYENS_PAI = ['ESPECES','MTN_MONEY','ORANGE_MONEY','WAVE','VIREMENT']
CANAUX     = ['GUICHET','EN_LIGNE']


class Command(BaseCommand):
    help = "Peuple la base avec des données de démonstration complètes"

    def handle(self, *args, **kwargs):
        self._creer_territoire()
        self._creer_centres()
        self._creer_villages()
        self._creer_rattachements()
        self._creer_agents()
        self._creer_individus_et_actes()
        self.stdout.write(self.style.SUCCESS("\n✅ Base de démonstration prête !"))

    # ── Territoire ────────────────────────────────────────────────────────────

    def _creer_territoire(self):
        from territoire.models import Region, Departement, Localite

        reg_map = {}
        for code, nom in REGIONS:
            r, _ = Region.objects.get_or_create(code=code, defaults={'nom': nom})
            reg_map[code] = r

        dep_map = {}
        for code, nom, reg_code in DEPARTEMENTS:
            d, _ = Departement.objects.get_or_create(
                code=code, defaults={'nom': nom, 'region': reg_map[reg_code]}
            )
            dep_map[code] = d

        loc_map = {}
        for code, nom, dep_code in LOCALITES:
            l, _ = Localite.objects.get_or_create(
                code=code, defaults={'nom': nom, 'departement': dep_map[dep_code]}
            )
            loc_map[code] = l

        self.loc_map = loc_map
        self.stdout.write("  Territoire créé.")

    def _creer_centres(self):
        from centres.models import Centre
        from territoire.models import Localite

        self.centre_map = {}
        for code, nom, type_c, loc_code in CENTRES:
            loc = Localite.objects.get(code=loc_code)
            c, _ = Centre.objects.get_or_create(
                code=code,
                defaults={
                    'nom': nom, 'type': type_c, 'localite': loc,
                    'date_creation': date(2020, 1, 1), 'actif': True,
                }
            )
            self.centre_map[code] = c
        self.stdout.write(f"  {len(self.centre_map)} centres créés.")

    def _creer_villages(self):
        from territoire.models import Village, Localite

        self.village_map = {}
        for code, nom, loc_code in VILLAGES_DATA:
            loc = Localite.objects.get(code=loc_code)
            v, _ = Village.objects.get_or_create(
                code=code, defaults={'nom': nom, 'localite': loc}
            )
            self.village_map[code] = v
        self.stdout.write(f"  {len(self.village_map)} villages créés.")

    def _creer_rattachements(self):
        from centres.models import RattachementVillage

        count = 0
        for centre_code, village_codes in RATTACHEMENTS.items():
            centre = self.centre_map[centre_code]
            for v_code in village_codes:
                village = self.village_map[v_code]
                _, created = RattachementVillage.objects.get_or_create(
                    centre=centre, village=village,
                    defaults={'date_debut': date(2020, 1, 1)}
                )
                if created:
                    count += 1
        self.stdout.write(f"  {count} rattachements créés.")

    # ── Agents ────────────────────────────────────────────────────────────────

    def _creer_agents(self):
        count = 0
        for email, pwd, nom, prenoms, matricule, centre_code in AGENTS:
            if Agent.objects.filter(email=email).exists():
                continue
            centre = self.centre_map[centre_code]
            Agent.objects.create_user(
                email=email, password=pwd, nom=nom, prenoms=prenoms,
                matricule=matricule, role='AGENT_CENTRE', centre=centre,
            )
            count += 1
        self.stdout.write(f"  {count} agents créés.")

    # ── Individus & Actes ─────────────────────────────────────────────────────

    def _creer_individus_et_actes(self):
        from individus.models import Individu
        from actes.models import (Acte, ActeNaissance, ActeMariage,
                                   ActeDeces, MentionMarginale)
        from paiements.models import Paiement, DemandeCopie
        from notifications.models import NotificationInterCentre

        if Individu.objects.count() > 10:
            self.stdout.write("  Individus déjà présents — ignoré.")
            return

        admin = Agent.objects.filter(role='ADMIN_CENTRAL').first()
        agents = {code: Agent.objects.filter(centre=c).first()
                  for code, c in self.centre_map.items()}

        today = date.today()
        individus_crees = []

        # ── 40 individus de base ───────────────────────────────────────────
        for i in range(40):
            sexe = 'M' if i % 2 == 0 else 'F'
            noms   = NOMS_M   if sexe == 'M' else NOMS_F
            prenom = PRENOMS_M if sexe == 'M' else PRENOMS_F
            annee  = random.randint(1970, 2005)
            mois   = random.randint(1, 12)
            jour   = random.randint(1, 28)
            nin = f"CI{annee}{str(uuid.uuid4().hex[:8]).upper()}"
            ind = Individu.objects.create(
                nin=nin,
                nom=random.choice(noms),
                prenoms=random.choice(prenom),
                sexe=sexe,
                date_naissance=date(annee, mois, jour),
                lieu_naissance_libelle=random.choice(
                    ['Abidjan','Bouaké','Daloa','Yamoussoukro','San-Pédro']),
                nationalite='CI',
            )
            individus_crees.append(ind)

        self.stdout.write(f"  {len(individus_crees)} individus créés.")

        # ── Actes de naissance ────────────────────────────────────────────
        centres_list = list(self.centre_map.values())
        villages_list = list(self.village_map.values())
        nb_naissance = 0

        for i, ind in enumerate(individus_crees[:30]):
            centre = centres_list[i % len(centres_list)]
            village = villages_list[i % len(villages_list)]
            agent = agents.get(
                [k for k, v in self.centre_map.items() if v == centre][0]
            ) or admin
            if not agent:
                continue

            evt_date = ind.date_naissance + timedelta(days=random.randint(1, 30))
            acte = Acte.objects.create(
                nature=Acte.NAISSANCE,
                statut=Acte.BROUILLON,
                individu=ind,
                centre=centre,
                village=village,
                date_evenement=evt_date,
                date_enregistrement=evt_date,
                agent=agent,
                numero_national=f"N-{centre.code}-{today.year}-{str(i+1).zfill(4)}",
                observations="Acte de naissance établi au centre.",
            )
            ActeNaissance.objects.create(
                acte=acte,
                heure_naissance=f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
                ordre_naissance=1,
                poids_naissance=round(random.uniform(2.8, 4.2), 3),
                etablissement=random.choice(['CHU','Maternité Publique','Clinique Privée','']),
                declarant_nom=random.choice(NOMS_M),
                declarant_prenoms=random.choice(PRENOMS_M),
                declarant_lien='Père',
                nom_pere=random.choice(NOMS_M),
                prenoms_pere=random.choice(PRENOMS_M),
                nationalite_pere='CI',
                profession_pere=random.choice(['Enseignant','Commerçant','Fonctionnaire','Agriculteur']),
                nom_mere=random.choice(NOMS_F),
                prenoms_mere=random.choice(PRENOMS_F),
                nationalite_mere='CI',
                profession_mere=random.choice(['Ménagère','Commerçante','Infirmière','Enseignante']),
            )
            # Valider 20 sur 30
            if i < 20:
                acte.statut = Acte.VALIDE
                acte.superviseur = admin
                acte.date_validation = timezone.now()
                acte.save()

            nb_naissance += 1

        self.stdout.write(f"  {nb_naissance} actes de naissance créés (20 validés, 10 brouillons).")

        # ── Actes de mariage ──────────────────────────────────────────────
        hommes  = [i for i in individus_crees if i.sexe == 'M'][:8]
        femmes  = [i for i in individus_crees if i.sexe == 'F'][:8]
        nb_mariage = 0

        for idx, (epoux, epouse) in enumerate(zip(hommes, femmes)):
            centre = centres_list[idx % len(centres_list)]
            agent = agents.get(
                [k for k, v in self.centre_map.items() if v == centre][0]
            ) or admin
            if not agent:
                continue

            evt_date = date(random.randint(2018, 2024), random.randint(1, 12),
                            random.randint(1, 28))
            acte = Acte.objects.create(
                nature=Acte.MARIAGE,
                statut=Acte.BROUILLON,
                individu=epoux,
                centre=centre,
                date_evenement=evt_date,
                date_enregistrement=evt_date,
                agent=agent,
                numero_national=f"M-{centre.code}-{today.year}-{str(idx+1).zfill(4)}",
            )
            ActeMariage.objects.create(
                acte=acte,
                epoux=epoux,
                epouse=epouse,
                regime_matrimonial=random.choice(['COMMUNAUTE_BIENS','SEPARATION_BIENS']),
                officiant_nom=f"Officier {idx+1}",
                temoin1_nom=random.choice(NOMS_M),
                temoin2_nom=random.choice(NOMS_F),
            )
            # Valider 5 sur 8
            if idx < 5:
                acte.statut = Acte.VALIDE
                acte.superviseur = admin
                acte.date_validation = timezone.now()
                acte.save()

                # 2 mariages avec mention DIVORCE
                if idx < 2:
                    MentionMarginale.objects.create(
                        acte=acte,
                        type_mention=MentionMarginale.DIVORCE,
                        date_mention=evt_date + timedelta(days=random.randint(200, 1000)),
                        observations="Divorce prononcé par le tribunal.",
                        agent=agent,
                    )

            nb_mariage += 1

        self.stdout.write(f"  {nb_mariage} actes de mariage créés (5 validés, 2 avec mention divorce).")

        # ── Actes de décès ────────────────────────────────────────────────
        decedes = individus_crees[32:38]
        nb_deces = 0

        for idx, ind in enumerate(decedes):
            centre = centres_list[idx % len(centres_list)]
            agent = agents.get(
                [k for k, v in self.centre_map.items() if v == centre][0]
            ) or admin
            if not agent:
                continue

            evt_date = date(random.randint(2022, 2024), random.randint(1, 12),
                            random.randint(1, 28))
            acte = Acte.objects.create(
                nature=Acte.DECES,
                statut=Acte.BROUILLON,
                individu=ind,
                centre=centre,
                date_evenement=evt_date,
                date_enregistrement=evt_date,
                agent=agent,
                numero_national=f"D-{centre.code}-{today.year}-{str(idx+1).zfill(4)}",
            )
            ActeDeces.objects.create(
                acte=acte,
                heure_deces=f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
                lieu_deces=random.choice(['CHU de Yopougon','Domicile','Clinique Saint-Anne-Marie']),
                cause_deces=random.choice(['Maladie','Accident','Causes naturelles']),
                declarant_nom=random.choice(NOMS_M),
                declarant_prenoms=random.choice(PRENOMS_M),
                declarant_lien='Fils',
            )
            ind.est_decede = True
            ind.date_deces = evt_date
            ind.save()

            if idx < 4:
                acte.statut = Acte.VALIDE
                acte.superviseur = admin
                acte.date_validation = timezone.now()
                acte.save()

            nb_deces += 1

        self.stdout.write(f"  {nb_deces} actes de décès créés (4 validés).")

        # ── Demandes de copie + Paiements ─────────────────────────────────
        actes_valides = Acte.objects.filter(statut=Acte.VALIDE)
        nb_demandes = 0
        nb_paiements = 0

        for idx, acte in enumerate(actes_valides[:25]):
            ref = f"DEM-{str(uuid.uuid4().hex[:8]).upper()}"
            canal = random.choice(CANAUX)
            demande = DemandeCopie.objects.create(
                reference=ref,
                acte=acte,
                demandeur_nom=random.choice(NOMS_M + NOMS_F),
                demandeur_cin=f"CI{random.randint(100000,999999)}",
                demandeur_lien=random.choice(['Intéressé','Père','Mère','Fils','Fille']),
                type_copie=random.choice(['EXTRAIT','COPIE_INTEGRALE','BULLETIN']),
                canal=canal,
                statut=random.choice(['EN_ATTENTE','TRAITE','LIVRE']),
                centre=acte.centre,
                date_demande=timezone.now() - timedelta(days=random.randint(1, 180)),
            )
            nb_demandes += 1

            # Paiement pour 20 demandes
            if idx < 20:
                Paiement.objects.create(
                    demande=demande,
                    montant=random.choice([500, 1000, 1500, 2000, 2500]),
                    devise='FCFA',
                    moyen=random.choice(MOYENS_PAI),
                    statut='VALIDE',
                    reference_externe=f"REF-{str(uuid.uuid4().hex[:10]).upper()}",
                    date_paiement=timezone.now() - timedelta(days=random.randint(1, 90)),
                    recu_numero=f"RECU-{str(idx+1).zfill(5)}",
                )
                nb_paiements += 1

        self.stdout.write(f"  {nb_demandes} demandes de copie, {nb_paiements} paiements créés.")

        # ── Notifications inter-centres ───────────────────────────────────
        actes_mariage_valides = Acte.objects.filter(
            nature=Acte.MARIAGE, statut=Acte.VALIDE
        )[:4]
        nb_notifs = 0

        for acte in actes_mariage_valides:
            centre_dest = random.choice(
                [c for c in centres_list if c != acte.centre]
            )
            NotificationInterCentre.objects.get_or_create(
                acte_declencheur=acte,
                centre_emetteur=acte.centre,
                centre_destinataire=centre_dest,
                defaults={
                    'type_evenement': 'MARIAGE',
                    'statut': random.choice(['ENVOYEE','ACQUITTEE']),
                    'payload': {
                        'individu_nom': f"{acte.individu.nom} {acte.individu.prenoms}",
                        'nature': 'MARIAGE',
                    },
                    'date_envoi': timezone.now(),
                }
            )
            nb_notifs += 1

        self.stdout.write(f"  {nb_notifs} notifications inter-centres créées.")
