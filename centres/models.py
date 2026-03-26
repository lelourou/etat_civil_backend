import uuid
from django.db import models


class Centre(models.Model):
    SOUS_PREFECTURE = 'SOUS_PREFECTURE'
    MAIRIE          = 'MAIRIE'
    TYPE_CHOICES    = [(SOUS_PREFECTURE, 'Sous-Préfecture'), (MAIRIE, 'Mairie')]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code            = models.CharField(max_length=20, unique=True)
    nom             = models.CharField(max_length=150)
    type            = models.CharField(max_length=20, choices=TYPE_CHOICES)
    localite        = models.ForeignKey('territoire.Localite', on_delete=models.PROTECT, related_name='centres')
    adresse         = models.TextField(blank=True)
    telephone       = models.CharField(max_length=20, blank=True)
    email           = models.EmailField(blank=True)
    actif           = models.BooleanField(default=True)
    date_creation   = models.DateField()
    date_fermeture  = models.DateField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'centres'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"


class RattachementVillage(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village     = models.ForeignKey('territoire.Village', on_delete=models.PROTECT, related_name='rattachements')
    centre      = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name='rattachements')
    date_debut  = models.DateField()
    date_fin    = models.DateField(null=True, blank=True)
    motif       = models.CharField(max_length=255, blank=True)
    decret_ref  = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rattachements_village'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.village.nom} → {self.centre.nom} ({self.date_debut})"

    @property
    def est_courant(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.date_fin is None or self.date_fin > today
