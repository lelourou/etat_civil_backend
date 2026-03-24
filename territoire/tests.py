from django.test import TestCase
from django.db import IntegrityError
from .models import Region, Departement, Localite, Village


class RegionModelTest(TestCase):
    def test_creation_et_str(self):
        region = Region.objects.create(code='RG01', nom='Abidjan')
        self.assertEqual(str(region), 'Abidjan')
        self.assertEqual(Region.objects.count(), 1)

    def test_code_unique(self):
        from django.db import transaction
        Region.objects.create(code='RG01', nom='Abidjan')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Region.objects.create(code='RG01', nom='Doublon')


class DepartementModelTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(code='RG01', nom='Abidjan')

    def test_creation_et_str(self):
        dept = Departement.objects.create(code='DP01', nom='Cocody', region=self.region)
        self.assertIn('Cocody', str(dept))
        self.assertIn('Abidjan', str(dept))

    def test_cascade_suppression_region(self):
        Departement.objects.create(code='DP01', nom='Cocody', region=self.region)
        self.region.delete()
        self.assertEqual(Departement.objects.count(), 0)


class LocaliteVillageTest(TestCase):
    def setUp(self):
        region = Region.objects.create(code='RG01', nom='Abidjan')
        departement = Departement.objects.create(code='DP01', nom='Cocody', region=region)
        self.localite = Localite.objects.create(code='LC01', nom='Riviera', departement=departement)

    def test_localite_str(self):
        self.assertEqual(str(self.localite), 'Riviera')

    def test_village_creation(self):
        village = Village.objects.create(code='VL01', nom='Quartier 3', localite=self.localite)
        self.assertIn('Riviera', str(village))
        self.assertEqual(Village.objects.count(), 1)

    def test_village_code_unique(self):
        from django.db import transaction
        Village.objects.create(code='VL01', nom='Quartier 3', localite=self.localite)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Village.objects.create(code='VL01', nom='Doublon', localite=self.localite)
