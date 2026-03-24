import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class AgentManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Agent.ADMIN_SYSTEME)
        return self.create_user(email, password, **extra_fields)


class Agent(AbstractBaseUser, PermissionsMixin):
    AGENT_GUICHET        = 'AGENT_GUICHET'
    SUPERVISEUR_CENTRE   = 'SUPERVISEUR_CENTRE'
    SUPERVISEUR_NATIONAL = 'SUPERVISEUR_NATIONAL'
    ADMIN_SYSTEME        = 'ADMIN_SYSTEME'

    ROLE_CHOICES = [
        (AGENT_GUICHET,        'Agent de guichet'),
        (SUPERVISEUR_CENTRE,   'Superviseur de centre'),
        (SUPERVISEUR_NATIONAL, 'Superviseur national'),
        (ADMIN_SYSTEME,        'Administrateur système'),
    ]

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email     = models.EmailField(unique=True)
    nom       = models.CharField(max_length=100)
    prenoms   = models.CharField(max_length=200)
    matricule = models.CharField(max_length=30, unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    role      = models.CharField(max_length=30, choices=ROLE_CHOICES, default=AGENT_GUICHET)
    centre    = models.ForeignKey(
        'centres.Centre',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='agents'
    )
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AgentManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nom', 'prenoms', 'matricule']

    class Meta:
        db_table            = 'agents'
        verbose_name        = 'Agent'
        verbose_name_plural = 'Agents'
        ordering            = ['nom', 'prenoms']

    def __str__(self):
        return f"{self.nom} {self.prenoms} ({self.get_role_display()})"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenoms}"
