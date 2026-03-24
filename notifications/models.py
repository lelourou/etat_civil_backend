import uuid
from django.db import models


class NotificationInterCentre(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    ENVOYEE    = 'ENVOYEE'
    ACQUITTEE  = 'ACQUITTEE'
    ECHOUEE    = 'ECHOUEE'
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'), (ENVOYEE, 'Envoyée'),
        (ACQUITTEE,  'Acquittée'),  (ECHOUEE, 'Échouée'),
    ]

    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    acte_declencheur      = models.ForeignKey('actes.Acte', on_delete=models.PROTECT,
                                               related_name='notifications_emises')
    centre_emetteur       = models.ForeignKey('centres.Centre', on_delete=models.PROTECT,
                                               related_name='notifications_emises')
    centre_destinataire   = models.ForeignKey('centres.Centre', on_delete=models.PROTECT,
                                               related_name='notifications_recues')
    acte_cible            = models.ForeignKey('actes.Acte', on_delete=models.SET_NULL,
                                               null=True, blank=True, related_name='notifications_recues')
    type_evenement        = models.CharField(max_length=50)
    payload               = models.JSONField(default=dict)
    statut                = models.CharField(max_length=15, choices=STATUT_CHOICES, default=EN_ATTENTE)
    tentatives            = models.PositiveSmallIntegerField(default=0)
    date_envoi            = models.DateTimeField(null=True, blank=True)
    date_acquittement     = models.DateTimeField(null=True, blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_intercentre'
        ordering = ['-created_at']

    def __str__(self):
        return (f"Notif {self.type_evenement}: "
                f"{self.centre_emetteur.code} → {self.centre_destinataire.code} "
                f"({self.get_statut_display()})")

    def acquitter(self):
        from django.utils import timezone
        self.statut           = self.ACQUITTEE
        self.date_acquittement = timezone.now()
        self.save(update_fields=['statut', 'date_acquittement'])
