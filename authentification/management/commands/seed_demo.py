"""
Commande : python manage.py seed_demo
Peuple la base avec ~2000 actes sur plusieurs années pour présentation.
Idempotente : skip si données déjà présentes.
"""
import random, uuid
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

Agent = get_user_model()

# ─── Référentiels ─────────────────────────────────────────────────────────────

REGIONS = [
    ('RG-AB','Abidjan'), ('RG-BK','Gbêkê'), ('RG-DL','Haut-Sassandra'),
    ('RG-YM','Yamoussoukro'), ('RG-MN','Tonkpi'), ('RG-KR','Kavally'),
]
DEPARTEMENTS = [
    ('DP-PL','Plateau','RG-AB'),   ('DP-AB','Abobo','RG-AB'),
    ('DP-YO','Yopougon','RG-AB'),  ('DP-CO','Cocody','RG-AB'),
    ('DP-BK','Bouaké','RG-BK'),    ('DP-DL','Daloa','RG-DL'),
    ('DP-YM','Yamoussoukro','RG-YM'), ('DP-MN','Man','RG-MN'),
]
LOCALITES = [
    ('LC-PL','Plateau','DP-PL'),   ('LC-AB','Abobo','DP-AB'),
    ('LC-YO','Yopougon','DP-YO'),  ('LC-CO','Cocody','DP-CO'),
    ('LC-BK','Bouaké','DP-BK'),    ('LC-DL','Daloa','DP-DL'),
    ('LC-YM','Yamoussoukro','DP-YM'), ('LC-MN','Man','DP-MN'),
]
CENTRES = [
    ('CTR-PL1','Mairie du Plateau',           'MAIRIE',          'LC-PL'),
    ('CTR-AB1',"Mairie d'Abobo",              'MAIRIE',          'LC-AB'),
    ('CTR-YO1','Sous-Préfecture de Yopougon', 'SOUS_PREFECTURE', 'LC-YO'),
    ('CTR-CO1','Sous-Préfecture de Cocody',   'SOUS_PREFECTURE', 'LC-CO'),
    ('CTR-BK1','Sous-Préfecture de Bouaké',   'SOUS_PREFECTURE', 'LC-BK'),
    ('CTR-DG1','Sous-Préfecture de Daloa',    'SOUS_PREFECTURE', 'LC-DL'),
    ('CTR-YM1','Mairie de Yamoussoukro',      'MAIRIE',          'LC-YM'),
    ('CTR-MN1','Sous-Préfecture de Man',      'SOUS_PREFECTURE', 'LC-MN'),
]
VILLAGES_DATA = [
    ('VL-PL1','Quartier Financier','LC-PL'), ('VL-PL2','Zone 4','LC-PL'),
    ('VL-AB1','Abobo-Baoulé','LC-AB'),       ('VL-AB2','Abobo-Gare','LC-AB'),
    ('VL-YO1','Yopougon-Attié','LC-YO'),     ('VL-YO2','Yopougon-Selmer','LC-YO'),
    ('VL-CO1','Riviera 2','LC-CO'),          ('VL-CO2','Angré','LC-CO'),
    ('VL-BK1','Bouaké-Centre','LC-BK'),      ('VL-BK2','Koko','LC-BK'),
    ('VL-DL1','Daloa-Centre','LC-DL'),       ('VL-DL2','Lobia','LC-DL'),
    ('VL-YM1','Quartier Millionnaire','LC-YM'),('VL-YM2',"N'Zué-Konan",'LC-YM'),
    ('VL-MN1','Man-Centre','LC-MN'),         ('VL-MN2','Bloleu','LC-MN'),
]
RATTACHEMENTS = {
    'CTR-PL1':['VL-PL1','VL-PL2'], 'CTR-AB1':['VL-AB1','VL-AB2'],
    'CTR-YO1':['VL-YO1','VL-YO2'], 'CTR-CO1':['VL-CO1','VL-CO2'],
    'CTR-BK1':['VL-BK1','VL-BK2'], 'CTR-DG1':['VL-DL1','VL-DL2'],
    'CTR-YM1':['VL-YM1','VL-YM2'], 'CTR-MN1':['VL-MN1','VL-MN2'],
}
AGENTS = [
    ('agent.abidjan@etatcivil.ci',  'Abidjan@2024',  'KOUAME', 'Jean-Baptiste','AGT-PL-001','CTR-PL1'),
    ('agent.abobo@etatcivil.ci',    'Abobo@2024',    'YAPI',   'Christelle',  'AGT-AB-001','CTR-AB1'),
    ('agent.yopougon@etatcivil.ci', 'Yopougon@2024', 'TRAORE', 'Moussa',      'AGT-YO-001','CTR-YO1'),
    ('agent.cocody@etatcivil.ci',   'Cocody@2024',   'ASSI',   'Vanessa',     'AGT-CO-001','CTR-CO1'),
    ('agent.bouake@etatcivil.ci',   'Bouake@2024',   'BAMBA',  'Aminata',     'AGT-BK-001','CTR-BK1'),
    ('agent.daloa@etatcivil.ci',    'Daloa@2024',    'GOBA',   'Emmanuel',    'AGT-DG-001','CTR-DG1'),
    ('agent.yamousso@etatcivil.ci', 'Yamousso@2024', 'KONE',   'Siaka',       'AGT-YM-001','CTR-YM1'),
    ('agent.man@etatcivil.ci',      'Man@2024',      'ZORO',   'Gervais',     'AGT-MN-001','CTR-MN1'),
]

NOMS   = ['KOUASSI','KONAN','BAMBA','TRAORE','KONE','OUATTARA','DIALLO','COULIBALY',
          'YAPI','GOBA','AKRE','SEKA','TAPE','DJET','GNAGNE','ASSI','TOURE','FOFANA',
          'AHOUA','YEBOUE','BLE','SERI','GNEBA','LAGO','KOUA','AKA','YAO','N\'GUESSAN',
          'GBAGBO','ACHI','OKOU','TANO','ADOU','ANOH','EHUI','ABOU','SILUE','DOUMBIA',
          'SANGARE','KOFFI','ATTA','BONI','SORO','DIARRASSOUBA','MEITE','BAKAYOKO']
PRENOMS_M = ['Jean-Baptiste','Kofi','Moussa','Ibrahim','Siaka','Emmanuel','Wilfried',
             'Narcisse','Brice','Franck','Rodrigue','Serge','Patrick','Ghislain','Romuald',
             'Arsène','Clovis','Thierry','Martial','Jérôme','Rodrigue','Constant',
             'Parfait','Florent','Gervais','Hyacinthe','Sylvestre','Aurèle','Fabrice']
PRENOMS_F = ['Aminata','Fatou','Christelle','Adjoua','Yolande','Sylvie','Marie-Claire',
             'Bintou','Rosine','Mariam','Cynthia','Estelle','Pauline','Aissatou','Evelyne',
             'Vanessa','Pulchérie','Grâce','Laeticia','Mireille','Séraphine','Bernadette',
             'Véronique','Claudine','Antoinette','Joséphine','Delphine','Nathalie']
PROFESSIONS= ['Enseignant(e)','Commerçant(e)','Fonctionnaire','Agriculteur/trice',
              'Infirmier(ère)','Chauffeur','Mécanicien','Couturier(ère)','Étudiant(e)',
              'Médecin','Avocat(e)','Ingénieur','Ménagère','Technicien(ne)','Comptable']
CAUSES_DECES = ['Paludisme','Accident de la route','Maladie cardiovasculaire',
                'Causes naturelles','Hypertension artérielle','Diabète','Septicémie',
                'Insuffisance rénale','AVC','Cancer']
ETABLISSEMENTS = ['CHU de Yopougon','CHU de Cocody','Maternité Publique d\'Abobo',
                  'Clinique Sainte-Marie','Clinique du Plateau','Maternité de Bouaké',
                  'CHR de Daloa','Hôpital Général de Man','Maternité de Yamoussoukro','']
MOYENS_PAI = ['ESPECES','MTN_MONEY','ORANGE_MONEY','WAVE','VIREMENT']
CANAUX     = ['GUICHET','EN_LIGNE']
TYPES_COPIE= ['EXTRAIT','COPIE_INTEGRALE','BULLETIN']
STATUTS_DEM= ['EN_ATTENTE','TRAITE','LIVRE']
LIEUX_DECES= ['CHU de Yopougon','CHU de Cocody','Domicile','Clinique Sainte-Marie',
              'CHR de Daloa','Hôpital Général de Man']
REGIMES    = ['COMMUNAUTE_BIENS','SEPARATION_BIENS']


def rdate(y_min, y_max):
    """Date aléatoire entre deux années."""
    start = date(y_min, 1, 1)
    end   = date(y_max, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def nin(annee):
    return f"CI{annee}{uuid.uuid4().hex[:8].upper()}"


class Command(BaseCommand):
    help = "Peuple la base avec ~2 000 actes sur plusieurs années"

    def handle(self, *args, **kwargs):
        self._geo()
        self._centres()
        self._villages()
        self._rattachements()
        self._agents()
        self._data()
        self.stdout.write(self.style.SUCCESS("\n✅ Seed terminé !"))

    # ── Géographie ────────────────────────────────────────────────────────────

    def _geo(self):
        from territoire.models import Region, Departement, Localite
        rm = {}
        for code, nom in REGIONS:
            r, _ = Region.objects.get_or_create(code=code, defaults={'nom': nom})
            rm[code] = r
        dm = {}
        for code, nom, rk in DEPARTEMENTS:
            d, _ = Departement.objects.get_or_create(code=code, defaults={'nom': nom,'region': rm[rk]})
            dm[code] = d
        self.lm = {}
        for code, nom, dk in LOCALITES:
            l, _ = Localite.objects.get_or_create(code=code, defaults={'nom': nom,'departement': dm[dk]})
            self.lm[code] = l
        self.stdout.write("  Géographie OK.")

    def _centres(self):
        from centres.models import Centre
        self.cm = {}
        for code, nom, typ, lk in CENTRES:
            c, _ = Centre.objects.get_or_create(
                code=code,
                defaults={'nom': nom,'type': typ,'localite': self.lm[lk],
                          'date_creation': date(2015,1,1),'actif': True}
            )
            self.cm[code] = c
        self.stdout.write(f"  {len(self.cm)} centres OK.")

    def _villages(self):
        from territoire.models import Village
        self.vm = {}
        for code, nom, lk in VILLAGES_DATA:
            v, _ = Village.objects.get_or_create(code=code, defaults={'nom': nom,'localite': self.lm[lk]})
            self.vm[code] = v
        self.stdout.write(f"  {len(self.vm)} villages OK.")

    def _rattachements(self):
        from centres.models import RattachementVillage
        n = 0
        for ck, vks in RATTACHEMENTS.items():
            for vk in vks:
                _, created = RattachementVillage.objects.get_or_create(
                    centre=self.cm[ck], village=self.vm[vk],
                    defaults={'date_debut': date(2015,1,1)}
                )
                if created: n += 1
        self.stdout.write(f"  {n} rattachements OK.")

    def _agents(self):
        n = 0
        for email, pwd, nom, prenoms, mat, ck in AGENTS:
            if not Agent.objects.filter(email=email).exists():
                Agent.objects.create_user(
                    email=email, password=pwd, nom=nom, prenoms=prenoms,
                    matricule=mat, role='AGENT_CENTRE', centre=self.cm[ck]
                )
                n += 1
        self.stdout.write(f"  {n} agents créés.")

    # ── Données métier ────────────────────────────────────────────────────────

    def _data(self):
        from individus.models import Individu
        from actes.models import (Acte, ActeNaissance, ActeMariage,
                                   ActeDeces, MentionMarginale)
        from paiements.models import Paiement, DemandeCopie
        from notifications.models import NotificationInterCentre

        if Acte.objects.count() > 50:
            self.stdout.write("  Actes déjà présents — ignoré.")
            return

        admin  = Agent.objects.filter(role='ADMIN_CENTRAL').first()
        agents = list(Agent.objects.filter(role='AGENT_CENTRE'))
        centres_list = list(self.cm.values())
        villages_list = list(self.vm.values())

        # ── Compteurs pour numéros ──
        cpt = {c.code: {'N':0,'M':0,'D':0} for c in centres_list}

        def next_num(centre, nature):
            cpt[centre.code][nature[0]] += 1
            n = cpt[centre.code][nature[0]]
            y = date.today().year
            return f"{nature[0]}-{centre.code}-{y}-{str(n).zfill(5)}"

        def agent_centre(centre):
            for a in agents:
                if a.centre_id == centre.id:
                    return a
            return admin

        # ══════════════════════════════════════════════════════════════════
        # 1. INDIVIDUS ADULTES (parents / époux / épouses / défunts)
        #    800 individus nés entre 1955 et 1995
        # ══════════════════════════════════════════════════════════════════
        adultes = []
        self.stdout.write("  Création des individus adultes…")
        for i in range(800):
            sexe    = 'M' if i % 2 == 0 else 'F'
            prenoms = PRENOMS_M if sexe == 'M' else PRENOMS_F
            annee   = random.randint(1955, 1995)
            ind = Individu.objects.create(
                nin=nin(annee),
                nom=random.choice(NOMS),
                prenoms=random.choice(prenoms),
                sexe=sexe,
                date_naissance=rdate(annee, annee),
                lieu_naissance_libelle=random.choice(
                    ['Abidjan','Bouaké','Daloa','Yamoussoukro','San-Pédro',
                     'Man','Korhogo','Abengourou','Divo','Bondoukou']),
                nationalite='CI',
            )
            adultes.append(ind)

        hommes_libres = [a for a in adultes if a.sexe == 'M']
        femmes_libres = [a for a in adultes if a.sexe == 'F']
        self.stdout.write(f"    {len(adultes)} adultes créés.")

        # ══════════════════════════════════════════════════════════════════
        # 2. ACTES DE NAISSANCE (1 200) — années 2015-2024
        # ══════════════════════════════════════════════════════════════════
        self.stdout.write("  Création des actes de naissance…")
        nb_n = 0
        enfants_par_annee = {}   # année → liste d'enfants (pour stats BI)

        for annee in range(2015, 2025):
            nb_cette_annee = random.randint(100, 140)
            enfants_par_annee[annee] = []
            for _ in range(nb_cette_annee):
                sexe    = random.choice(['M','F'])
                prenoms = PRENOMS_M if sexe == 'M' else PRENOMS_F
                centre  = random.choice(centres_list)
                village = random.choice([v for k,v in self.vm.items()
                                         if k in RATTACHEMENTS.get(centre.code,[])]
                                        or villages_list)
                agent   = agent_centre(centre)
                evt     = rdate(annee, annee)

                # Créer l'enfant
                enfant = Individu.objects.create(
                    nin=nin(annee),
                    nom=random.choice(NOMS),
                    prenoms=random.choice(prenoms),
                    sexe=sexe,
                    date_naissance=evt,
                    lieu_naissance_village=village,
                    lieu_naissance_libelle=village.nom,
                    nationalite='CI',
                    centre_naissance=centre,
                )
                enfants_par_annee[annee].append(enfant)

                # Acte
                acte = Acte(
                    nature=Acte.NAISSANCE,
                    statut=Acte.BROUILLON,
                    individu=enfant,
                    centre=centre,
                    village=village,
                    date_evenement=evt,
                    date_enregistrement=evt + timedelta(days=random.randint(1,15)),
                    agent=agent,
                    numero_national=next_num(centre,'NAISSANCE'),
                    observations='',
                )
                # 85 % validés
                if random.random() < 0.85:
                    acte.statut      = Acte.VALIDE
                    acte.superviseur = admin
                    acte.date_validation = timezone.now()
                acte.save()

                pere   = random.choice(hommes_libres)
                mere   = random.choice(femmes_libres)
                ActeNaissance.objects.create(
                    acte=acte,
                    heure_naissance=f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
                    ordre_naissance=random.choice([1,1,1,2]),
                    poids_naissance=round(random.uniform(2.5,4.5),3),
                    etablissement=random.choice(ETABLISSEMENTS),
                    declarant_nom=pere.nom, declarant_prenoms=pere.prenoms,
                    declarant_lien='Père', declarant_cin=f"CI{random.randint(100000,999999)}",
                    nom_pere=pere.nom,    prenoms_pere=pere.prenoms,
                    nationalite_pere='CI',profession_pere=random.choice(PROFESSIONS),
                    nom_mere=mere.nom,    prenoms_mere=mere.prenoms,
                    nationalite_mere='CI',profession_mere=random.choice(PROFESSIONS),
                )
                nb_n += 1

        self.stdout.write(f"    {nb_n} actes de naissance créés.")

        # ══════════════════════════════════════════════════════════════════
        # 3. ACTES DE MARIAGE (500) — années 2015-2024
        # ══════════════════════════════════════════════════════════════════
        self.stdout.write("  Création des actes de mariage…")
        nb_m   = 0
        maries = []   # (epoux, epouse, acte) pour les mentions divorce

        h_pool = list(hommes_libres)
        f_pool = list(femmes_libres)
        random.shuffle(h_pool)
        random.shuffle(f_pool)
        pairs = list(zip(h_pool[:250], f_pool[:250]))  # 250 couples uniques * 2 actes/couple = 500

        for annee in range(2015, 2025):
            nb_cette_annee = random.randint(45, 55)
            for _ in range(nb_cette_annee):
                if not pairs:
                    break
                epoux, epouse = pairs.pop()
                centre  = random.choice(centres_list)
                agent   = agent_centre(centre)
                evt     = rdate(annee, annee)

                acte = Acte(
                    nature=Acte.MARIAGE,
                    statut=Acte.BROUILLON,
                    individu=epoux,
                    centre=centre,
                    date_evenement=evt,
                    date_enregistrement=evt + timedelta(days=random.randint(1,7)),
                    agent=agent,
                    numero_national=next_num(centre,'MARIAGE'),
                )
                if random.random() < 0.80:
                    acte.statut      = Acte.VALIDE
                    acte.superviseur = admin
                    acte.date_validation = timezone.now()
                acte.save()

                ActeMariage.objects.create(
                    acte=acte,
                    epoux=epoux, epouse=epouse,
                    regime_matrimonial=random.choice(REGIMES),
                    officiant_nom=f"{random.choice(NOMS)} {random.choice(PRENOMS_M)}",
                    temoin1_nom=random.choice(NOMS),
                    temoin1_cin=f"CI{random.randint(100000,999999)}",
                    temoin2_nom=random.choice(NOMS),
                    temoin2_cin=f"CI{random.randint(100000,999999)}",
                )
                if acte.statut == Acte.VALIDE:
                    maries.append((epoux, epouse, acte, evt))
                nb_m += 1

        # Mentions DIVORCE sur ~20 % des mariages validés
        nb_div = 0
        for epoux, epouse, acte_mar, evt_mar in random.sample(maries, min(80, len(maries))):
            MentionMarginale.objects.create(
                acte=acte_mar,
                type_mention=MentionMarginale.DIVORCE,
                date_mention=evt_mar + timedelta(days=random.randint(365,3000)),
                observations="Divorce prononcé par jugement du tribunal.",
                agent=agent_centre(acte_mar.centre),
            )
            nb_div += 1

        self.stdout.write(f"    {nb_m} actes de mariage créés ({nb_div} mentions divorce).")

        # ══════════════════════════════════════════════════════════════════
        # 4. ACTES DE DÉCÈS (300) — années 2018-2024
        # ══════════════════════════════════════════════════════════════════
        self.stdout.write("  Création des actes de décès…")
        nb_d  = 0
        pool_deces = [a for a in adultes if not a.est_decede]
        random.shuffle(pool_deces)
        pool_deces = pool_deces[:300]

        for annee in range(2018, 2025):
            nb_cette_annee = random.randint(35, 50)
            for _ in range(nb_cette_annee):
                if not pool_deces:
                    break
                ind    = pool_deces.pop()
                centre = random.choice(centres_list)
                agent  = agent_centre(centre)
                evt    = rdate(annee, annee)

                acte = Acte(
                    nature=Acte.DECES,
                    statut=Acte.BROUILLON,
                    individu=ind,
                    centre=centre,
                    date_evenement=evt,
                    date_enregistrement=evt + timedelta(days=random.randint(1,10)),
                    agent=agent,
                    numero_national=next_num(centre,'DECES'),
                )
                if random.random() < 0.80:
                    acte.statut      = Acte.VALIDE
                    acte.superviseur = admin
                    acte.date_validation = timezone.now()
                acte.save()

                ActeDeces.objects.create(
                    acte=acte,
                    heure_deces=f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
                    lieu_deces=random.choice(LIEUX_DECES),
                    cause_deces=random.choice(CAUSES_DECES),
                    declarant_nom=random.choice(NOMS),
                    declarant_prenoms=random.choice(PRENOMS_M+PRENOMS_F),
                    declarant_lien=random.choice(['Fils','Fille','Époux','Épouse','Frère','Sœur']),
                    declarant_cin=f"CI{random.randint(100000,999999)}",
                )
                ind.est_decede = True
                ind.date_deces = evt
                ind.save(update_fields=['est_decede','date_deces'])
                nb_d += 1

        self.stdout.write(f"    {nb_d} actes de décès créés.")

        # ══════════════════════════════════════════════════════════════════
        # 5. DEMANDES DE COPIE + PAIEMENTS
        # ══════════════════════════════════════════════════════════════════
        self.stdout.write("  Création des demandes et paiements…")
        actes_valides = list(Acte.objects.filter(statut=Acte.VALIDE).order_by('?')[:800])
        nb_dem = 0
        nb_pai = 0
        montants = [500,1000,1000,1500,2000,2000,2500,3000]

        for acte in actes_valides:
            ref    = f"DEM-{uuid.uuid4().hex[:8].upper()}"
            canal  = random.choice(CANAUX)
            statut = random.choices(STATUTS_DEM, weights=[20,40,40])[0]
            d_dem  = acte.date_evenement + timedelta(days=random.randint(10,730))
            demande = DemandeCopie.objects.create(
                reference=ref,
                acte=acte,
                demandeur_nom=random.choice(NOMS),
                demandeur_cin=f"CI{random.randint(100000,999999)}",
                demandeur_lien=random.choice(['Intéressé','Père','Mère','Fils','Fille','Employeur']),
                type_copie=random.choice(TYPES_COPIE),
                canal=canal,
                statut=statut,
                centre=acte.centre,
                date_demande=timezone.make_aware(
                    __import__('datetime').datetime(d_dem.year, d_dem.month, d_dem.day)
                ),
            )
            nb_dem += 1

            # 85 % ont un paiement
            if random.random() < 0.85:
                Paiement.objects.create(
                    demande=demande,
                    montant=random.choice(montants),
                    devise='FCFA',
                    moyen=random.choice(MOYENS_PAI),
                    statut='VALIDE',
                    reference_externe=f"REF-{uuid.uuid4().hex[:10].upper()}",
                    date_paiement=timezone.make_aware(
                        __import__('datetime').datetime(d_dem.year, d_dem.month, d_dem.day)
                    ),
                    recu_numero=f"RECU-{str(nb_pai+1).zfill(6)}",
                )
                nb_pai += 1

        self.stdout.write(f"    {nb_dem} demandes, {nb_pai} paiements créés.")

        # ══════════════════════════════════════════════════════════════════
        # 6. NOTIFICATIONS INTER-CENTRES
        # ══════════════════════════════════════════════════════════════════
        actes_notif = list(Acte.objects.filter(
            nature__in=[Acte.MARIAGE, Acte.DECES], statut=Acte.VALIDE
        ).order_by('?')[:120])

        nb_notif = 0
        for acte in actes_notif:
            autres = [c for c in centres_list if c.id != acte.centre_id]
            if not autres:
                continue
            dest = random.choice(autres)
            NotificationInterCentre.objects.get_or_create(
                acte_declencheur=acte,
                centre_emetteur=acte.centre,
                centre_destinataire=dest,
                defaults={
                    'type_evenement': acte.nature,
                    'statut': random.choices(
                        ['ENVOYEE','ACQUITTEE'], weights=[40,60])[0],
                    'payload': {
                        'individu_nom': f"{acte.individu.nom} {acte.individu.prenoms}",
                        'nature': acte.nature,
                    },
                    'date_envoi': timezone.now(),
                }
            )
            nb_notif += 1

        self.stdout.write(f"    {nb_notif} notifications inter-centres créées.")

        # ── Résumé final ─────────────────────────────────────────────────
        from actes.models import Acte as A
        total = A.objects.count()
        self.stdout.write(f"\n  📊 Total actes en base : {total}")
        self.stdout.write(f"     Naissances : {A.objects.filter(nature='NAISSANCE').count()}")
        self.stdout.write(f"     Mariages   : {A.objects.filter(nature='MARIAGE').count()}")
        self.stdout.write(f"     Décès      : {A.objects.filter(nature='DECES').count()}")
        self.stdout.write(f"     Validés    : {A.objects.filter(statut='VALIDE').count()}")
        self.stdout.write(f"     Brouillons : {A.objects.filter(statut='BROUILLON').count()}")
