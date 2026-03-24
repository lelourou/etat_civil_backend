import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tests_utils import creer_centre, creer_agent, creer_superviseur, creer_individu
from actes.models import Acte
from .models import DemandeCopie, Paiement


def creer_acte_valide(centre, agent, superviseur, individu):
    acte = Acte.objects.create(
        nature=Acte.NAISSANCE,
        individu=individu,
        centre=centre,
        date_evenement=datetime.date(2024, 1, 1),
        agent=agent,
    )
    acte.valider(superviseur=superviseur)
    return acte


def creer_demande(acte, centre):
    return DemandeCopie.objects.create(
        acte=acte,
        centre=centre,
        demandeur_nom='KONE Aminata',
        type_copie=DemandeCopie.COPIE_INTEGRALE,
        canal=DemandeCopie.GUICHET,
    )


class DemandeCopieTest(TestCase):
    def setUp(self):
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.superviseur = creer_superviseur(
            centre=self.centre, email='sup@test.ci', matricule='SUP-001'
        )
        self.individu = creer_individu(self.centre)
        self.acte = creer_acte_valide(self.centre, self.agent, self.superviseur, self.individu)

    def test_reference_auto_generee(self):
        demande = creer_demande(self.acte, self.centre)
        self.assertTrue(demande.reference.startswith('DEM-'))
        self.assertIn('2026', demande.reference)

    def test_statut_initial_en_attente_paiement(self):
        demande = creer_demande(self.acte, self.centre)
        self.assertEqual(demande.statut, DemandeCopie.EN_ATTENTE_PAIEMENT)

    def test_str_demande(self):
        demande = creer_demande(self.acte, self.centre)
        self.assertIn('DEM-', str(demande))

    def test_reference_unique(self):
        d1 = creer_demande(self.acte, self.centre)
        # Simuler un deuxième enregistrement — la référence doit être différente
        individu2 = creer_individu(self.centre, nin='NIN-002', nom='BAMBA', prenoms='Sali')
        acte2 = creer_acte_valide(self.centre, self.agent, self.superviseur, individu2)
        d2 = creer_demande(acte2, self.centre)
        self.assertNotEqual(d1.reference, d2.reference)


class PaiementTest(TestCase):
    def setUp(self):
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.superviseur = creer_superviseur(
            centre=self.centre, email='sup@test.ci', matricule='SUP-001'
        )
        self.individu = creer_individu(self.centre)
        self.acte = creer_acte_valide(self.centre, self.agent, self.superviseur, self.individu)
        self.demande = creer_demande(self.acte, self.centre)

    def test_montant_defaut_500_fcfa(self):
        paiement = Paiement.objects.create(
            demande=self.demande,
            moyen=Paiement.ESPECES,
        )
        self.assertEqual(float(paiement.montant), 500.0)
        self.assertEqual(paiement.devise, 'XOF')

    def test_statut_initial_en_attente(self):
        paiement = Paiement.objects.create(
            demande=self.demande,
            moyen=Paiement.MTN_MONEY,
        )
        self.assertEqual(paiement.statut, Paiement.EN_ATTENTE)

    def test_str_paiement(self):
        paiement = Paiement.objects.create(
            demande=self.demande,
            moyen=Paiement.WAVE,
        )
        self.assertIn('500', str(paiement))
        self.assertIn('XOF', str(paiement))


class PaiementAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.superviseur = creer_superviseur(
            centre=self.centre, email='sup@test.ci', matricule='SUP-001'
        )
        self.individu = creer_individu(self.centre)
        self.acte = creer_acte_valide(self.centre, self.agent, self.superviseur, self.individu)
        self.demande = creer_demande(self.acte, self.centre)
        self.client.force_authenticate(user=self.agent)

    def test_list_demandes(self):
        resp = self.client.get('/api/v1/paiements/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)
