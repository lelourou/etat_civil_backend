from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, DepartementViewSet, LocaliteViewSet, VillageViewSet

router = DefaultRouter()
router.register('regions',      RegionViewSet,      basename='region')
router.register('departements', DepartementViewSet, basename='departement')
router.register('localites',    LocaliteViewSet,    basename='localite')
router.register('villages',     VillageViewSet,     basename='village')

urlpatterns = [path('', include(router.urls))]
