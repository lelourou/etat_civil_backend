import uuid
from django.db import models


class DemandeCopie(models.Model):
    GUICHET   = 'GUICHET'
    EN_LIGNE  = 'EN_LIGNE'
    CANAL_CHOICES = [(GUICHET, 'Guichet'), (EN_LIGNE, 'En ligne')]

    EN_ATTENTE_PAIEMENT = 'EN_ATTENTE_PAIEMENT'
    PAYEE       = 'PAYEE'
    EN_COURS    = 'EN_COURS'
    DELIVREE    = 'DELIVREE'
    REJETEE     = 'REJETEE'
    STATUT_CHOICES = [
        (EN_ATTENTE_PAIEMENT, 'En attente de paiement'),
        (PAYEE,    'Payée'),
        (EN_COURS, 'En cours de traitement'),
        (DELIVREE, 'Délivrée'),
        (REJETEE,  'Rejetée'),
    ]

    COPIE_INTEGRALE           = 'COPIE_INTEGRALE'
    EXTRAIT_AVEC_FILIATION    = 'EXTRAIT_AVEC_FILIATION'
    EXTRAIT_SANS_FILIATION    = 'EXTRAIT_SANS_FILIATION'
    BULLETIN                  = 'BULLETIN'
    TYPE_COPIE_CHOICES = [
        (COPIE_INTEGRALE,        'Copie intégrale'),
        (EXTRAIT_AVEC_FILIATION, 'Extrait avec filiation'),
        (EXTRAIT_SANS_FILIATION, 'Extrait sans filiation'),
        (BULLETIN,               'Bulletin'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference      = models.CharField(max_length=30, unique=True)
    acte           = models.ForeignKey('actes.Acte', on_delete=models.PROTECT, related_name='demandes_copie')
    demandeur_nom  = models.CharField(max_length=200)
    demandeur_cin  = models.CharField(max_length=30, blank=True)
    demandeur_lien = models.CharField(max_length=100, blank=True)
    type_copie     = models.CharField(max_length=30, choices=TYPE_COPIE_CHOICES)
    canal          = models.CharField(max_length=10, choices=CANAL_CHOICES)
    statut         = models.CharField(max_length=25, choices=STATUT_CHOICES, default=EN_ATTENTE_PAIEMENT)
    centre         = models.ForeignKey('centres.Centre', on_delete=models.PROTECT, related_name='demandes_copie')
    date_demande   = models.DateTimeField(auto_now_add=True)
    date_livraison = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'demandes_copie'
        ordering = ['-date_demande']

    def __str__(self):
        return f"Demande {self.reference} — {self.get_statut_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from django.utils import timezone
            count = DemandeCopie.objects.count() + 1
            self.reference = f"DEM-{timezone.now().year}-{str(count).zfill(9)}"
        super().save(*args, **kwargs)


class Paiement(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    CONFIRME   = 'CONFIRME'
    ECHOUE     = 'ECHOUE'
    REMBOURSE  = 'REMBOURSE'
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'), (CONFIRME, 'Confirmé'),
        (ECHOUE, 'Échoué'), (REMBOURSE, 'Remboursé'),
    ]

    MTN_MONEY    = 'MTN_MONEY'
    ORANGE_MONEY = 'ORANGE_MONEY'
    WAVE         = 'WAVE'
    ESPECES      = 'ESPECES'
    VIREMENT     = 'VIREMENT'
    MOYEN_CHOICES = [
        (MTN_MONEY, 'MTN Money'), (ORANGE_MONEY, 'Orange Money'),
        (WAVE, 'Wave'), (ESPECES, 'Espèces'), (VIREMENT, 'Virement'),
    ]

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demande            = models.OneToOneField(DemandeCopie, on_delete=models.CASCADE, related_name='paiement')
    montant            = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    devise             = models.CharField(max_length=5, default='XOF')
    moyen              = models.CharField(max_length=15, choices=MOYEN_CHOICES)
    statut             = models.CharField(max_length=15, choices=STATUT_CHOICES, default=EN_ATTENTE)
    reference_externe  = models.CharField(max_length=100, blank=True)
    date_paiement      = models.DateTimeField(null=True, blank=True)
    recu_numero        = models.CharField(max_length=50, unique=True, blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'paiements'
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement {self.montant} {self.devise} — {self.get_statut_display()}"
