import uuid
from django.db import models
from django.core.exceptions import ValidationError


def generer_numero_national(nature, centre_code):
    from django.utils import timezone
    from actes.models import Acte
    annee   = timezone.now().year
    prefixe = {'NAISSANCE': 'NAI', 'MARIAGE': 'MAR', 'DECES': 'DEC'}.get(nature, 'ACT')
    count   = Acte.objects.filter(nature=nature, centre__code=centre_code).count() + 1
    return f"CI-{prefixe}-{annee}-{centre_code}-{str(count).zfill(9)}"


class Acte(models.Model):
    NAISSANCE = 'NAISSANCE'
    MARIAGE   = 'MARIAGE'
    DECES     = 'DECES'
    NATURE_CHOICES = [(NAISSANCE, 'Naissance'), (MARIAGE, 'Mariage'), (DECES, 'Décès')]

    BROUILLON  = 'BROUILLON'
    VALIDE     = 'VALIDE'
    VERROUILLE = 'VERROUILLE'
    ANNULE     = 'ANNULE'
    STATUT_CHOICES = [
        (BROUILLON,  'Brouillon'),
        (VALIDE,     'Validé'),
        (VERROUILLE, 'Verrouillé'),
        (ANNULE,     'Annulé'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_national     = models.CharField(max_length=40, unique=True, blank=True)
    nature              = models.CharField(max_length=15, choices=NATURE_CHOICES)
    statut              = models.CharField(max_length=15, choices=STATUT_CHOICES, default=BROUILLON)
    individu            = models.ForeignKey('individus.Individu', on_delete=models.PROTECT, related_name='actes')
    centre              = models.ForeignKey('centres.Centre', on_delete=models.PROTECT, related_name='actes')
    village             = models.ForeignKey('territoire.Village', on_delete=models.SET_NULL, null=True, blank=True)
    date_evenement      = models.DateField()
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    agent               = models.ForeignKey('authentification.Agent', on_delete=models.PROTECT,
                                            related_name='actes_crees')
    superviseur         = models.ForeignKey('authentification.Agent', on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name='actes_valides')
    date_validation     = models.DateTimeField(null=True, blank=True)
    hash_contenu        = models.CharField(max_length=64, blank=True)
    observations        = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'actes'
        ordering = ['-date_evenement']
        indexes  = [
            models.Index(fields=['individu', 'nature']),
            models.Index(fields=['centre', 'nature']),
            models.Index(fields=['statut']),
            models.Index(fields=['numero_national']),
        ]

    def __str__(self):
        return f"{self.numero_national} — {self.get_nature_display()} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.numero_national:
            self.numero_national = generer_numero_national(self.nature, self.centre.code)
        super().save(*args, **kwargs)

    def clean(self):
        if self.individu.est_decede and self.nature != self.DECES:
            raise ValidationError("Impossible de créer un acte pour un individu décédé.")

    def valider(self, superviseur):
        from django.utils import timezone
        self.statut          = self.VALIDE
        self.superviseur     = superviseur
        self.date_validation = timezone.now()
        self.save()
        if self.nature == self.DECES:
            self._appliquer_verrou_deces()

    def _appliquer_verrou_deces(self):
        individu = self.individu
        individu.est_decede  = True
        individu.date_deces  = self.date_evenement
        individu.save(update_fields=['est_decede', 'date_deces', 'updated_at'])
        Acte.objects.filter(individu=individu).exclude(pk=self.pk).update(statut=self.VERROUILLE)


class ActeNaissance(models.Model):
    acte              = models.OneToOneField(Acte, on_delete=models.CASCADE,
                                             primary_key=True, related_name='detail_naissance')
    heure_naissance   = models.TimeField(null=True, blank=True)
    ordre_naissance   = models.PositiveSmallIntegerField(default=1)
    poids_naissance   = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    etablissement     = models.CharField(max_length=200, blank=True)
    declarant_nom     = models.CharField(max_length=200)
    declarant_prenoms = models.CharField(max_length=200)
    declarant_lien    = models.CharField(max_length=50, blank=True)
    declarant_cin     = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = 'actes_naissance'


class ActeMariage(models.Model):
    acte                        = models.OneToOneField(Acte, on_delete=models.CASCADE,
                                                       primary_key=True, related_name='detail_mariage')
    epoux                       = models.ForeignKey('individus.Individu', on_delete=models.PROTECT,
                                                     related_name='mariages_epoux')
    epouse                      = models.ForeignKey('individus.Individu', on_delete=models.PROTECT,
                                                     related_name='mariages_epouse')
    regime_matrimonial          = models.CharField(max_length=100, blank=True)
    temoin1_nom                 = models.CharField(max_length=200, blank=True)
    temoin1_cin                 = models.CharField(max_length=30, blank=True)
    temoin2_nom                 = models.CharField(max_length=200, blank=True)
    temoin2_cin                 = models.CharField(max_length=30, blank=True)
    officiant_nom               = models.CharField(max_length=200, blank=True)
    acte_naissance_epoux_ref    = models.CharField(max_length=40, blank=True)
    acte_naissance_epouse_ref   = models.CharField(max_length=40, blank=True)

    class Meta:
        db_table = 'actes_mariage'

    def clean(self):
        if self.epoux == self.epouse:
            raise ValidationError("L'époux et l'épouse ne peuvent pas être la même personne.")


class ActeDeces(models.Model):
    acte              = models.OneToOneField(Acte, on_delete=models.CASCADE,
                                             primary_key=True, related_name='detail_deces')
    heure_deces       = models.TimeField(null=True, blank=True)
    lieu_deces        = models.CharField(max_length=200, blank=True)
    cause_deces       = models.CharField(max_length=500, blank=True)
    declarant_nom     = models.CharField(max_length=200)
    declarant_prenoms = models.CharField(max_length=200)
    declarant_lien    = models.CharField(max_length=50, blank=True)
    declarant_cin     = models.CharField(max_length=30, blank=True)
    acte_naissance_ref= models.CharField(max_length=40, blank=True)

    class Meta:
        db_table = 'actes_deces'


class MentionMarginale(models.Model):
    MARIAGE        = 'MARIAGE'
    DIVORCE        = 'DIVORCE'
    DECES          = 'DECES'
    RECONNAISSANCE = 'RECONNAISSANCE'
    ADOPTION       = 'ADOPTION'
    RECTIFICATION  = 'RECTIFICATION'
    TYPE_CHOICES   = [
        (MARIAGE, 'Mariage'), (DIVORCE, 'Divorce'), (DECES, 'Décès'),
        (RECONNAISSANCE, 'Reconnaissance'), (ADOPTION, 'Adoption'),
        (RECTIFICATION, 'Rectification'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    acte             = models.ForeignKey(Acte, on_delete=models.CASCADE, related_name='mentions')
    type_mention     = models.CharField(max_length=20, choices=TYPE_CHOICES)
    acte_source_ref  = models.CharField(max_length=40, blank=True)
    centre_source    = models.ForeignKey('centres.Centre', on_delete=models.SET_NULL,
                                         null=True, blank=True)
    date_mention     = models.DateField()
    contenu          = models.TextField()
    agent            = models.ForeignKey('authentification.Agent', on_delete=models.PROTECT)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mentions_marginales'
        ordering = ['-date_mention']

    def __str__(self):
        return f"{self.get_type_mention_display()} sur acte {self.acte.numero_national}"
