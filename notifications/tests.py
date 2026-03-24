import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tests_utils import creer_centre, creer_agent, creer_superviseur, creer_individu
from actes.models import Acte
from .models import NotificationInterCentre


def creer_centres_distincts():
    from territoire.models import Region, Departement, Localite
    region = Region.objects.create(code='RG01', nom='Région A')
    dept = Departement.objects.create(code='DP01', nom='Dept A', region=region)
    loc1 = Localite.objects.create(code='LC01', nom='Loc A', departement=dept)
    loc2 = Localite.objects.create(code='LC02', nom='Loc B', departement=dept)
    from centres.models import Centre
    c1 = Centre.objects.create(code='CTR01', nom='Centre A', type=Centre.SOUS_PREFECTURE,
                               localite=loc1, date_creation=datetime.date(2020, 1, 1))
    c2 = Centre.objects.create(code='CTR02', nom='Centre B', type=Centre.MAIRIE,
                               localite=loc2, date_creation=datetime.date(2020, 1, 1))
    return c1, c2


class NotificationModelTest(TestCase):
    def setUp(self):
        self.centre_a, self.centre_b = creer_centres_distincts()
        self.agent = creer_agent(centre=self.centre_a)
        self.superviseur = creer_superviseur(
            centre=self.centre_a, email='sup@test.ci', matricule='SUP-001'
        )
        self.individu = creer_individu(self.centre_a)
        self.acte = Acte.objects.create(
            nature=Acte.MARIAGE,
            individu=self.individu,
            centre=self.centre_a,
            date_evenement=datetime.date(2024, 6, 15),
            agent=self.agent,
        )

    def _creer_notification(self):
        return NotificationInterCentre.objects.create(
            acte_declencheur=self.acte,
            centre_emetteur=self.centre_a,
            centre_destinataire=self.centre_b,
            type_evenement='MARIAGE_INTER_CENTRE',
            payload={'acte_id': str(self.acte.id)},
        )

    def test_creation_notification(self):
        notif = self._creer_notification()
        self.assertEqual(notif.statut, NotificationInterCentre.EN_ATTENTE)
        self.assertEqual(notif.tentatives, 0)
        self.assertIn('CTR01', str(notif))
        self.assertIn('CTR02', str(notif))

    def test_acquitter_notification(self):
        """R5 — L'acquittement met à jour statut et date."""
        notif = self._creer_notification()
        notif.statut = NotificationInterCentre.ENVOYEE
        notif.save(update_fields=['statut'])

        notif.acquitter()
        notif.refresh_from_db()

        self.assertEqual(notif.statut, NotificationInterCentre.ACQUITTEE)
        self.assertIsNotNone(notif.date_acquittement)

    def test_payload_json(self):
        notif = self._creer_notification()
        self.assertIn('acte_id', notif.payload)


class NotificationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.centre_a, self.centre_b = creer_centres_distincts()
        self.agent_a = creer_agent(centre=self.centre_a, email='agent_a@test.ci', matricule='AGT-001')
        # Agent du centre destinataire — verra la notification via le filtre RBAC
        self.agent_b = creer_agent(centre=self.centre_b, email='agent_b@test.ci', matricule='AGT-002')
        self.individu = creer_individu(self.centre_a)
        self.acte = Acte.objects.create(
            nature=Acte.MARIAGE,
            individu=self.individu,
            centre=self.centre_a,
            date_evenement=datetime.date(2024, 6, 15),
            agent=self.agent_a,
        )
        # La notification est destinée à centre_b → agent_b la verra
        self.notif = NotificationInterCentre.objects.create(
            acte_declencheur=self.acte,
            centre_emetteur=self.centre_a,
            centre_destinataire=self.centre_b,
            type_evenement='MARIAGE_INTER_CENTRE',
        )
        self.client.force_authenticate(user=self.agent_b)

    def test_list_notifications(self):
        resp = self.client.get('/api/v1/notifications/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_acquitter_via_api(self):
        resp = self.client.post(f'/api/v1/notifications/{self.notif.id}/acquitter/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.notif.refresh_from_db()
        self.assertEqual(self.notif.statut, NotificationInterCentre.ACQUITTEE)
