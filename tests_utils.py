"""
Helpers partagés entre tous les tests — crée les objets de base (territoire, centre, agent, individu).
"""
import datetime
from territoire.models import Region, Departement, Localite, Village
from centres.models import Centre
from authentification.models import Agent
from individus.models import Individu


def creer_region(code='RG01', nom='Région Abidjan'):
    return Region.objects.create(code=code, nom=nom)


def creer_departement(region=None, code='DP01', nom='Département Cocody'):
    if region is None:
        region = creer_region()
    return Departement.objects.create(code=code, nom=nom, region=region)


def creer_localite(departement=None, code='LC01', nom='Cocody'):
    if departement is None:
        departement = creer_departement()
    return Localite.objects.create(code=code, nom=nom, departement=departement)


def creer_village(localite=None, code='VL01', nom='Riviera'):
    if localite is None:
        localite = creer_localite()
    return Village.objects.create(code=code, nom=nom, localite=localite)


def creer_centre(localite=None, code='CTR01', nom='Centre Cocody'):
    if localite is None:
        localite = creer_localite()
    return Centre.objects.create(
        code=code,
        nom=nom,
        type=Centre.SOUS_PREFECTURE,
        localite=localite,
        date_creation=datetime.date(2020, 1, 1),
    )


def creer_agent(centre=None, email='agent@test.ci', matricule='AGT-001',
                role=Agent.AGENT_GUICHET, password='Test@2024ci'):
    if centre is None:
        centre = creer_centre()
    return Agent.objects.create_user(
        email=email,
        password=password,
        nom='KONAN',
        prenoms='Kouame',
        matricule=matricule,
        role=role,
        centre=centre,
    )


def creer_superviseur(centre=None, email='superviseur@test.ci', matricule='SUP-001'):
    return creer_agent(
        centre=centre,
        email=email,
        matricule=matricule,
        role=Agent.SUPERVISEUR_CENTRE,
    )


def creer_individu(centre=None, nin='NIN-TEST-001', nom='KOUAME', prenoms='Jean',
                   date_naissance=None):
    if centre is None:
        centre = creer_centre()
    if date_naissance is None:
        date_naissance = datetime.date(1990, 5, 15)
    return Individu.objects.create(
        nin=nin,
        nom=nom,
        prenoms=prenoms,
        sexe=Individu.M,
        date_naissance=date_naissance,
        lieu_naissance_libelle='Abidjan',
        centre_naissance=centre,
    )
