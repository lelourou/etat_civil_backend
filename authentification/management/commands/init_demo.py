"""
Commande : python manage.py init_demo
Crée les comptes de démonstration (admin + 3 agents) si absents.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

Agent = get_user_model()


class Command(BaseCommand):
    help = "Initialise les comptes de démonstration"

    def handle(self, *args, **kwargs):
        self._creer_admin()
        self._creer_agents()

    def _creer_admin(self):
        if Agent.objects.filter(email='admin@etatcivil.ci').exists():
            self.stdout.write("Admin déjà existant.")
            return
        Agent.objects.create_superuser(
            email='admin@etatcivil.ci',
            password='Admin@2024',
            nom='ADMINISTRATEUR',
            prenoms='Central',
            matricule='ADMIN-001',
            role='ADMIN_CENTRAL',
        )
        self.stdout.write(self.style.SUCCESS("Admin créé : admin@etatcivil.ci"))

    def _creer_agents(self):
        try:
            from centres.models import Centre
        except ImportError:
            return

        agents_demo = [
            {
                'email': 'agent.abidjan@etatcivil.ci',
                'password': 'Abidjan@2024',
                'nom': 'KOUAME',
                'prenoms': 'Jean-Baptiste',
                'matricule': 'AGT-PL-001',
                'centre_code': 'CTR-PL1',
            },
            {
                'email': 'agent.bouake@etatcivil.ci',
                'password': 'Bouake@2024',
                'nom': 'BAMBA',
                'prenoms': 'Aminata',
                'matricule': 'AGT-BK-001',
                'centre_code': 'CTR-BK1',
            },
            {
                'email': 'agent.daloa@etatcivil.ci',
                'password': 'Daloa@2024',
                'nom': 'GOBA',
                'prenoms': 'Emmanuel',
                'matricule': 'AGT-DG-001',
                'centre_code': 'CTR-DG1',
            },
        ]

        for data in agents_demo:
            if Agent.objects.filter(email=data['email']).exists():
                continue
            try:
                centre = Centre.objects.get(code=data['centre_code'])
            except Centre.DoesNotExist:
                self.stdout.write(f"Centre {data['centre_code']} introuvable — agent ignoré.")
                continue
            Agent.objects.create_user(
                email=data['email'],
                password=data['password'],
                nom=data['nom'],
                prenoms=data['prenoms'],
                matricule=data['matricule'],
                role='AGENT_CENTRE',
                centre=centre,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Agent créé : {data['email']} — {centre.nom}"
            ))
