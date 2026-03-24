import uuid
import hashlib
from django.db import models


def calculer_hash_biographique(nom, prenoms, date_naissance, lieu_naissance=''):
    contenu = "|".join([
        nom.lower().strip(),
        prenoms.lower().strip(),
        str(date_naissance),
        (lieu_naissance or '').lower().strip(),
    ])
    return hashlib.sha256(contenu.encode()).hexdigest()


class Individu(models.Model):
    M = 'M'
    F = 'F'
    SEXE_CHOICES = [(M, 'Masculin'), (F, 'Féminin')]

    id                      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nin                     = models.CharField(max_length=20, unique=True)
    nom                     = models.CharField(max_length=100)
    prenoms                 = models.CharField(max_length=200)
    sexe                    = models.CharField(max_length=1, choices=SEXE_CHOICES)
    date_naissance          = models.DateField()
    lieu_naissance_village  = models.ForeignKey(
        'territoire.Village', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='individus_nes'
    )
    lieu_naissance_libelle  = models.CharField(max_length=200, blank=True)
    nationalite             = models.CharField(max_length=100, default='Ivoirienne')
    centre_naissance        = models.ForeignKey(
        'centres.Centre', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='individus_nes'
    )
    hash_biographique       = models.CharField(max_length=64, unique=True)
    est_decede              = models.BooleanField(default=False)
    date_deces              = models.DateField(null=True, blank=True)
    created_at              = models.DateTimeField(auto_now_add=True)
    updated_at              = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'individus'
        ordering = ['nom', 'prenoms']
        indexes  = [
            models.Index(fields=['nom', 'prenoms']),
            models.Index(fields=['date_naissance']),
            models.Index(fields=['hash_biographique']),
        ]

    def __str__(self):
        return f"{self.nom} {self.prenoms} — NIN: {self.nin}"

    def save(self, *args, **kwargs):
        self.hash_biographique = calculer_hash_biographique(
            self.nom, self.prenoms, self.date_naissance, self.lieu_naissance_libelle
        )
        super().save(*args, **kwargs)

    @classmethod
    def verifier_doublon(cls, nom, prenoms, date_naissance, lieu_naissance='', exclude_id=None):
        h = calculer_hash_biographique(nom, prenoms, date_naissance, lieu_naissance)
        qs = cls.objects.filter(hash_biographique=h)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.first()


class Filiation(models.Model):
    PERE  = 'PERE'
    MERE  = 'MERE'
    ROLE_CHOICES = [(PERE, 'Père'), (MERE, 'Mère')]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enfant          = models.ForeignKey(Individu, on_delete=models.CASCADE, related_name='filiations')
    parent          = models.ForeignKey(Individu, on_delete=models.SET_NULL, null=True, blank=True, related_name='enfants')
    role            = models.CharField(max_length=10, choices=ROLE_CHOICES)
    nom_libelle     = models.CharField(max_length=200, blank=True)
    prenoms_libelle = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'filiations'
        unique_together = [('enfant', 'role')]

    def __str__(self):
        return f"{self.get_role_display()} de {self.enfant}"
