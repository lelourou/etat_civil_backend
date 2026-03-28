"""
Commande : python manage.py init_demo
Crée l'administrateur central si la base est vide.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

Agent = get_user_model()


class Command(BaseCommand):
    help = "Initialise le compte administrateur de démonstration"

    def handle(self, *args, **kwargs):
        if Agent.objects.filter(email='admin@etatcivil.ci').exists():
            self.stdout.write("Admin déjà existant — rien à faire.")
            return

        Agent.objects.create_superuser(
            email='admin@etatcivil.ci',
            password='Admin@2024',
            nom='ADMINISTRATEUR',
            prenoms='Central',
            matricule='ADMIN-001',
            role='ADMIN_CENTRAL',
        )
        self.stdout.write(self.style.SUCCESS(
            "Admin créé : admin@etatcivil.ci / Admin@2024"
        ))
