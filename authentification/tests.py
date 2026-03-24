from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tests_utils import creer_centre, creer_agent
from .models import Agent


class AgentModelTest(TestCase):
    def setUp(self):
        self.centre = creer_centre()

    def test_creation_agent(self):
        agent = creer_agent(centre=self.centre)
        self.assertEqual(str(agent), 'KONAN Kouame (Agent de guichet)')
        self.assertEqual(agent.nom_complet, 'KONAN Kouame')
        self.assertTrue(agent.is_active)

    def test_email_unique(self):
        from django.db import IntegrityError, transaction
        creer_agent(centre=self.centre)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                creer_agent(centre=self.centre, matricule='AGT-002')

    def test_superuser_creation(self):
        superuser = Agent.objects.create_superuser(
            email='admin@test.ci',
            password='Admin@2024ci',
            nom='ADMIN',
            prenoms='Sys',
            matricule='ADM-001',
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertEqual(superuser.role, Agent.ADMIN_SYSTEME)

    def test_password_is_hashed(self):
        agent = creer_agent(centre=self.centre)
        self.assertNotEqual(agent.password, 'Test@2024ci')
        self.assertTrue(agent.check_password('Test@2024ci'))


class LoginAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.centre = creer_centre()
        self.agent = creer_agent(centre=self.centre, password='Test@2024ci')

    def test_login_valide_retourne_tokens(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'email': 'agent@test.ci',
            'password': 'Test@2024ci',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_invalide_retourne_401(self):
        resp = self.client.post('/api/v1/auth/login/', {
            'email': 'agent@test.ci',
            'password': 'mauvais_mdp',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_authentifie(self):
        self.client.force_authenticate(user=self.agent)
        resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['email'], 'agent@test.ci')

    def test_me_non_authentifie(self):
        resp = self.client.get('/api/v1/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blackliste_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.agent)
        self.client.force_authenticate(user=self.agent)
        resp = self.client.post('/api/v1/auth/logout/', {
            'refresh': str(refresh),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
