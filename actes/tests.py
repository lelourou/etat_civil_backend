import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from tests_utils import creer_centre, creer_agent, creer_superviseur, creer_individu
from .models import Acte, ActeNaissance


def creer_acte(agent, individu, centre, nature=Acte.NAISSANCE):
    return Acte.objects.create(
        nature=nature,
        individu=individu,
        centre=centre,
        date_evenement=datetime.date(2024, 3, 1),
        agent=agent,
    )


class ActeCreationTest(TestCase):
    def setUp(self):
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.individu = creer_individu(self.centre)

    def test_numero_national_auto_genere(self):
        acte = creer_acte(self.agent, self.individu, self.centre)
        self.assertTrue(acte.numero_national.startswith('CI-NAI-'))
        self.assertIn('CTR01', acte.numero_national)

    def test_statut_par_defaut_brouillon(self):
        acte = creer_acte(self.agent, self.individu, self.centre)
        self.assertEqual(acte.statut, Acte.BROUILLON)

    def test_str_acte(self):
        acte = creer_acte(self.agent, self.individu, self.centre)
        self.assertIn('Naissance', str(acte))
        self.assertIn('Brouillon', str(acte))

    def test_numero_incremente_par_nature(self):
        a1 = creer_acte(self.agent, self.individu, self.centre, Acte.NAISSANCE)
        individu2 = creer_individu(self.centre, nin='NIN-002', nom='DIALLO', prenoms='Moussa')
        a2 = creer_acte(self.agent, individu2, self.centre, Acte.NAISSANCE)
        self.assertNotEqual(a1.numero_national, a2.numero_national)

    def test_creation_acte_individu_decede_leve_erreur(self):
        self.individu.est_decede = True
        self.individu.save(update_fields=['est_decede', 'updated_at'])
        acte = Acte(
            nature=Acte.NAISSANCE,
            individu=self.individu,
            centre=self.centre,
            date_evenement=datetime.date(2024, 3, 1),
            agent=self.agent,
        )
        with self.assertRaises(ValidationError):
            acte.clean()


class ActeValidationTest(TestCase):
    def setUp(self):
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.superviseur = creer_superviseur(
            centre=self.centre,
            email='superviseur@test.ci',
            matricule='SUP-001',
        )
        self.individu = creer_individu(self.centre)

    def test_valider_acte_change_statut(self):
        acte = creer_acte(self.agent, self.individu, self.centre)
        acte.valider(superviseur=self.superviseur)
        acte.refresh_from_db()
        self.assertEqual(acte.statut, Acte.VALIDE)
        self.assertEqual(acte.superviseur, self.superviseur)
        self.assertIsNotNone(acte.date_validation)

    def test_r6_valider_deces_marque_individu_decede(self):
        """R6 — Validation d'un acte de décès : individu.est_decede = True."""
        acte_deces = creer_acte(self.agent, self.individu, self.centre, Acte.DECES)
        acte_deces.valider(superviseur=self.superviseur)
        self.individu.refresh_from_db()
        self.assertTrue(self.individu.est_decede)
        self.assertEqual(self.individu.date_deces, acte_deces.date_evenement)

    def test_r6_valider_deces_verrouille_autres_actes(self):
        """R6 — Les autres actes de l'individu passent à VERROUILLE."""
        acte_naissance = creer_acte(self.agent, self.individu, self.centre, Acte.NAISSANCE)
        acte_naissance.statut = Acte.VALIDE
        acte_naissance.save(update_fields=['statut'])

        acte_deces = creer_acte(self.agent, self.individu, self.centre, Acte.DECES)
        acte_deces.valider(superviseur=self.superviseur)

        acte_naissance.refresh_from_db()
        self.assertEqual(acte_naissance.statut, Acte.VERROUILLE)

    def test_r6_acte_deces_lui_meme_reste_valide(self):
        """R6 — L'acte de décès lui-même reste VALIDE (non verrouillé)."""
        acte_deces = creer_acte(self.agent, self.individu, self.centre, Acte.DECES)
        acte_deces.valider(superviseur=self.superviseur)
        acte_deces.refresh_from_db()
        self.assertEqual(acte_deces.statut, Acte.VALIDE)


class ActeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.superviseur = creer_superviseur(
            centre=self.centre,
            email='superviseur@test.ci',
            matricule='SUP-001',
        )
        self.individu = creer_individu(self.centre)
        self.client.force_authenticate(user=self.agent)

    def test_list_actes(self):
        creer_acte(self.agent, self.individu, self.centre)
        resp = self.client.get('/api/v1/actes/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_valider_acte_via_api(self):
        acte = creer_acte(self.agent, self.individu, self.centre)
        self.client.force_authenticate(user=self.superviseur)
        resp = self.client.post(f'/api/v1/actes/{acte.id}/valider/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['statut'], Acte.VALIDE)

    def test_valider_acte_deja_valide_retourne_400(self):
        acte = creer_acte(self.agent, self.individu, self.centre)
        acte.valider(superviseur=self.superviseur)
        self.client.force_authenticate(user=self.superviseur)
        resp = self.client.post(f'/api/v1/actes/{acte.id}/valider/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_par_nature(self):
        creer_acte(self.agent, self.individu, self.centre, Acte.NAISSANCE)
        resp = self.client.get('/api/v1/actes/?nature=NAISSANCE')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data['results']:
            self.assertEqual(item['nature'], 'NAISSANCE')
