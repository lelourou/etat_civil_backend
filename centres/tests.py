import datetime
from django.test import TestCase
from django.db import IntegrityError
from tests_utils import creer_localite, creer_centre, creer_village
from .models import Centre, RattachementVillage


class CentreModelTest(TestCase):
    def setUp(self):
        self.localite = creer_localite()

    def test_creation_et_str(self):
        centre = creer_centre(localite=self.localite)
        self.assertIn('Centre Cocody', str(centre))
        self.assertIn('Sous-Préfecture', str(centre))

    def test_code_unique(self):
        from django.db import transaction
        creer_centre(localite=self.localite)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Centre.objects.create(
                    code='CTR01', nom='Doublon',
                    type=Centre.MAIRIE, localite=self.localite,
                    date_creation=datetime.date(2020, 1, 1),
                )

    def test_actif_par_defaut(self):
        centre = creer_centre(localite=self.localite)
        self.assertTrue(centre.actif)


class RattachementVillageTest(TestCase):
    def setUp(self):
        self.centre = creer_centre()
        # Réutilise la même localite pour éviter les conflits de codes uniques
        self.village = creer_village(localite=self.centre.localite)

    def test_creation_rattachement(self):
        r = RattachementVillage.objects.create(
            village=self.village,
            centre=self.centre,
            date_debut=datetime.date(2020, 1, 1),
        )
        self.assertIn(self.village.nom, str(r))
        self.assertIn(self.centre.nom, str(r))

    def test_est_courant_sans_date_fin(self):
        r = RattachementVillage.objects.create(
            village=self.village,
            centre=self.centre,
            date_debut=datetime.date(2020, 1, 1),
        )
        self.assertTrue(r.est_courant)

    def test_est_courant_date_fin_passee(self):
        r = RattachementVillage.objects.create(
            village=self.village,
            centre=self.centre,
            date_debut=datetime.date(2020, 1, 1),
            date_fin=datetime.date(2021, 1, 1),
        )
        self.assertFalse(r.est_courant)
