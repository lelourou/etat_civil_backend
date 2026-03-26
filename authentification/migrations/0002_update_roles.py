from django.db import migrations


def migrer_roles(apps, schema_editor):
    """
    Convertit les anciens rôles vers les deux nouveaux :
    - ADMIN_SYSTEME, SUPERVISEUR_NATIONAL → ADMIN_CENTRAL
    - AGENT_GUICHET, SUPERVISEUR_CENTRE   → AGENT_CENTRE
    """
    Agent = apps.get_model('authentification', 'Agent')
    Agent.objects.filter(role__in=['ADMIN_SYSTEME', 'SUPERVISEUR_NATIONAL']).update(role='ADMIN_CENTRAL')
    Agent.objects.filter(role__in=['AGENT_GUICHET', 'SUPERVISEUR_CENTRE']).update(role='AGENT_CENTRE')


class Migration(migrations.Migration):

    dependencies = [
        ('authentification', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrer_roles, migrations.RunPython.noop),
    ]
