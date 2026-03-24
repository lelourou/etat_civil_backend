import datetime
import hashlib
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tests_utils import creer_centre, creer_agent, creer_individu
from .models import Individu, calculer_hash_biographique


class HashBiographiqueTest(TestCase):
    """R1 — Hash SHA-256 anti-doublon."""

    def test_hash_calcule_correctement(self):
        contenu = "kouame|jean|1990-05-15|abidjan"
        attendu = hashlib.sha256(contenu.encode()).hexdigest()
        self.assertEqual(
            calculer_hash_biographique('KOUAME', 'Jean', datetime.date(1990, 5, 15), 'Abidjan'),
            attendu,
        )

    def test_hash_insensible_a_la_casse(self):
        h1 = calculer_hash_biographique('KOUAME', 'Jean', datetime.date(1990, 5, 15), 'Abidjan')
        h2 = calculer_hash_biographique('kouame', 'JEAN', datetime.date(1990, 5, 15), 'ABIDJAN')
        self.assertEqual(h1, h2)

    def test_hash_calcule_a_la_sauvegarde(self):
        centre = creer_centre()
        individu = creer_individu(centre=centre)
        attendu = calculer_hash_biographique(
            individu.nom, individu.prenoms,
            individu.date_naissance, individu.lieu_naissance_libelle,
        )
        self.assertEqual(individu.hash_biographique, attendu)
        self.assertEqual(len(individu.hash_biographique), 64)

    def test_hash_change_si_prenoms_different(self):
        h1 = calculer_hash_biographique('KOUAME', 'Jean', datetime.date(1990, 5, 15))
        h2 = calculer_hash_biographique('KOUAME', 'Paul', datetime.date(1990, 5, 15))
        self.assertNotEqual(h1, h2)


class DoublonDetectionTest(TestCase):
    """R1 — Détection de doublons."""

    def setUp(self):
        self.centre = creer_centre()
        self.individu = creer_individu(self.centre)

    def test_verifier_doublon_trouve_existant(self):
        resultat = Individu.verifier_doublon(
            self.individu.nom,
            self.individu.prenoms,
            self.individu.date_naissance,
            self.individu.lieu_naissance_libelle,
        )
        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.id, self.individu.id)

    def test_verifier_doublon_retourne_none_si_absent(self):
        resultat = Individu.verifier_doublon('AUTRE', 'Nom', datetime.date(1985, 3, 10))
        self.assertIsNone(resultat)

    def test_verifier_doublon_exclude_soi_meme(self):
        resultat = Individu.verifier_doublon(
            self.individu.nom,
            self.individu.prenoms,
            self.individu.date_naissance,
            self.individu.lieu_naissance_libelle,
            exclude_id=self.individu.id,
        )
        self.assertIsNone(resultat)

    def test_hash_unique_en_base(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Individu.objects.create(
                nin='NIN-TEST-002',
                nom=self.individu.nom,
                prenoms=self.individu.prenoms,
                sexe=Individu.M,
                date_naissance=self.individu.date_naissance,
                lieu_naissance_libelle=self.individu.lieu_naissance_libelle,
            )


class IndividuAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre)
        self.client.force_authenticate(user=self.agent)

    def test_list_individus(self):
        creer_individu(self.centre)
        resp = self.client.get('/api/v1/individus/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_list_non_authentifie(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/individus/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_recherche_par_nom(self):
        creer_individu(self.centre, nin='NIN-001', nom='BAMBA', prenoms='Ali')
        creer_individu(self.centre, nin='NIN-002', nom='TRAORE', prenoms='Sali')
        resp = self.client.get('/api/v1/individus/?search=BAMBA')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        noms = [r['nom'] for r in resp.data['results']]
        self.assertIn('BAMBA', noms)
        self.assertNotIn('TRAORE', noms)
