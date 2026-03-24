import uuid
from django.db import models


class Region(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code       = models.CharField(max_length=10, unique=True)
    nom        = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'regions'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Departement(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code       = models.CharField(max_length=10, unique=True)
    nom        = models.CharField(max_length=100)
    region     = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='departements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departements'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"


class Localite(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code         = models.CharField(max_length=20, unique=True)
    nom          = models.CharField(max_length=100)
    departement  = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='localites')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'localites'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Village(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code       = models.CharField(max_length=20, unique=True)
    nom        = models.CharField(max_length=100)
    localite   = models.ForeignKey(Localite, on_delete=models.CASCADE, related_name='villages')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'villages'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.localite.nom})"
